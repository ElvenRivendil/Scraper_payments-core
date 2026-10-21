# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsDistributionToSya/application/operations/SystemWalletsDistributionToSyaWriteOperation.py */

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, AccountType, LedgerEntry, Transaction
from app.models.enums import LedgerEntryDirection, TransactionStatus, TransactionType
from app.scripe.application.services.SystemWalletProvisioningService import (
    SystemWalletProvisioningService,
)
from app.services.audit import write_audit_event
from app.services.balances import account_balances_minor, account_posted_balance_minor
from app.services.transfers import create_transfer
from app.schemas import TransferCreate
from app.services.SystemWalletsDistributionToSya.domain.config.SystemWalletsDistributionToSyaConfig import (
    SystemWalletsDistributionToSyaConfig,
)
from app.services.SystemWalletsDistributionToSya.domain.strategies.SystemWalletsDistributionToSyaAllocationCalculator import (
    SystemWalletsDistributionToSyaAllocationCalculator,
)


class SystemWalletsDistributionToSyaWriteOperation:
    IDEMPOTENCY_PREFIX = "system_wallets_distribution_to_sya"
    DESCRIPTION_PREFIX = "System wallets distribution to SYA"

    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        execution_time: datetime,
        user_ids: list[UUID],
        user_er_balances_minor: dict[UUID, tuple[int, int, int]],
        er_total_minor: int,
        distribution_amount_minor: int,
    ) -> dict[str, int]:
        if execution_time.tzinfo is None:
            raise ValueError("Execution time must be timezone-aware.")
        if er_total_minor < 0 or distribution_amount_minor < 0:
            raise ValueError("Amounts must not be negative.")

        config = SystemWalletsDistributionToSyaConfig
        config.validate()
        system_owner_id = SystemWalletProvisioningService.SYSTEM_OWNER_ID
        unique_user_ids = tuple(sorted(set(user_ids), key=str))
        if set(user_er_balances_minor) != set(unique_user_ids):
            raise ValueError("Snapshot users do not match the active user list.")

        allocation_result = SystemWalletsDistributionToSyaAllocationCalculator.calculate(
            user_er_balances_minor,
            distribution_amount_minor,
        )
        if allocation_result["er_total_minor"] != er_total_minor:
            raise ValueError("ER total does not match the supplied snapshot.")

        required_wallet_codes = (
            config.SYSTEM_TOTAL_WALLET_CODE,
            config.SYSTEM_DISTRIBUTION_WALLET_CODE,
            config.USER_DESTINATION_WALLET_CODE,
        )
        wallet_condition = (
            (Account.owner_id == system_owner_id)
            & Account.wallet_code.in_(
                (config.SYSTEM_TOTAL_WALLET_CODE, config.SYSTEM_DISTRIBUTION_WALLET_CODE)
            )
        )
        user_destination_condition = (
            Account.owner_id.in_(unique_user_ids)
            & (Account.wallet_code == config.USER_DESTINATION_WALLET_CODE)
        )
        locked_accounts = session.scalars(
            select(Account)
            .where(wallet_condition | user_destination_condition)
            .order_by(Account.owner_id, Account.wallet_code, Account.id)
            .with_for_update()
        ).all()

        system_accounts: dict[str, Account] = {}
        destination_accounts: dict[UUID, Account] = {}
        for account in locked_accounts:
            if account.currency_code != config.CURRENCY_CODE:
                raise ValueError(f"Wallet {account.wallet_code} has unexpected currency.")
            if account.type != AccountType.USER:
                raise ValueError(f"Wallet {account.wallet_code} must have type USER.")
            if account.owner_id == system_owner_id:
                if not account.is_system:
                    raise ValueError(f"System wallet {account.wallet_code} is not marked as system.")
                if account.wallet_code in system_accounts:
                    raise ValueError(f"Duplicate system wallet: {account.wallet_code}.")
                system_accounts[account.wallet_code] = account
            else:
                if account.is_system or account.owner_id not in unique_user_ids:
                    raise ValueError(f"User wallet {account.wallet_code} has invalid ownership.")
                if account.owner_id in destination_accounts:
                    raise ValueError(f"Duplicate user wallet {account.wallet_code}.")
                destination_accounts[account.owner_id] = account

        missing_system = set(required_wallet_codes[:2]) - set(system_accounts)
        if missing_system:
            raise ValueError("Required system wallets are missing: " + ", ".join(sorted(missing_system)) + ".")
        missing_users = set(unique_user_ids) - set(destination_accounts)
        if missing_users:
            raise ValueError(f"Active users are missing SYA wallets: {len(missing_users)}.")

        system_total = system_accounts[config.SYSTEM_TOTAL_WALLET_CODE]
        system_distribution = system_accounts[config.SYSTEM_DISTRIBUTION_WALLET_CODE]
        current_distribution_available = account_balances_minor(
            session,
            system_distribution.id,
        )[2]
        if current_distribution_available != distribution_amount_minor:
            raise ValueError("SPAP available balance changed after the snapshot.")

        execution_hour = execution_time.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S")
        virtual_key = f"{cls.IDEMPOTENCY_PREFIX}:virtual:{execution_hour}"
        existing_virtual = session.execute(
            select(Transaction).where(Transaction.idempotency_key == virtual_key)
        ).scalar_one_or_none()
        if existing_virtual is not None:
            raise ValueError("A distribution transaction already exists for this execution time.")

        previous_total_balance = account_posted_balance_minor(session, system_total.id)
        delta_minor = er_total_minor - previous_total_balance
        if delta_minor:
            transaction_id = uuid4()
            session.add(
                Transaction(
                    id=transaction_id,
                    type=TransactionType.VIRTUAL_CONSOLIDATION,
                    status=TransactionStatus.POSTED,
                    currency_code=config.CURRENCY_CODE,
                    idempotency_key=virtual_key,
                    description=(
                        f"{cls.DESCRIPTION_PREFIX} "
                        f"{config.USER_SOURCE_WALLET_CODE} -> "
                        f"{config.SYSTEM_TOTAL_WALLET_CODE} {execution_hour}"
                    ),
                )
            )
            session.flush()
            session.add(
                LedgerEntry(
                    tx_id=transaction_id,
                    account_id=system_total.id,
                    currency_code=config.CURRENCY_CODE,
                    direction=(
                        LedgerEntryDirection.CREDIT
                        if delta_minor > 0
                        else LedgerEntryDirection.DEBIT
                    ),
                    amount=abs(delta_minor),
                )
            )
            write_audit_event(
                session,
                event_type="system_wallets_distribution_to_sya_virtual",
                entity_type="transaction",
                entity_id=str(transaction_id),
                payload_json={
                    "source_wallet_code": config.USER_SOURCE_WALLET_CODE,
                    "destination_wallet_code": config.SYSTEM_TOTAL_WALLET_CODE,
                    "er_total_minor": er_total_minor,
                    "previous_destination_balance_minor": previous_total_balance,
                    "delta_minor": delta_minor,
                    "currency_code": config.CURRENCY_CODE,
                    "execution_time": execution_time.isoformat(),
                    "virtual": True,
                    "source_debits_created": False,
                    "system_owner_id": str(system_owner_id),
                },
            )

        prelocked_accounts = {
            account.id: account
            for account in (*system_accounts.values(), *destination_accounts.values())
        }
        allocations = allocation_result["allocations_minor"]
        transfer_count = 0
        transferred_minor = 0
        for owner_id in unique_user_ids:
            amount_minor = allocations[owner_id]
            if amount_minor <= 0:
                continue
            destination = destination_accounts[owner_id]
            result = create_transfer(
                session,
                idempotency_key=f"{cls.IDEMPOTENCY_PREFIX}:transfer:{execution_hour}:{owner_id}",
                transfer=TransferCreate(
                    from_account_id=system_distribution.id,
                    to_account_id=destination.id,
                    amount_minor=amount_minor,
                    currency_code=config.CURRENCY_CODE,
                    description=f"{cls.DESCRIPTION_PREFIX} SPAP -> SYA {execution_hour}",
                ),
                owner_id=system_owner_id,
                scope=cls.IDEMPOTENCY_PREFIX,
                commit=False,
                prelocked_accounts=prelocked_accounts,
            )
            if not result.created:
                raise ValueError("An unexpected idempotency replay occurred during distribution.")
            transfer_count += 1
            transferred_minor += amount_minor

        if transferred_minor != distribution_amount_minor:
            raise ValueError("Transferred total does not match the distribution amount.")

        return {
            "er_total_minor": er_total_minor,
            "distribution_amount_minor": distribution_amount_minor,
            "transfer_count": transfer_count,
            "transferred_minor": transferred_minor,
            "virtual_delta_minor": delta_minor,
        }
