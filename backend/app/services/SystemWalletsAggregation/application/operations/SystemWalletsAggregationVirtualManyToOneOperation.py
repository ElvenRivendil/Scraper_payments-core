# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsAggregation/application/operations/SystemWalletsAggregationVirtualManyToOneOperation.py */

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, LedgerEntry, Transaction
from app.models.enums import LedgerEntryDirection, TransactionStatus, TransactionType
from app.services.audit import write_audit_event
from app.services.balances import account_posted_balance_minor
from app.services.SystemFundsConsolidation.application.services.SystemFundsConsolidationWalletValidator import (
    SystemFundsConsolidationWalletValidator,
)
from app.services.SystemWalletsAggregation.domain.config.SystemWalletsAggregationConfig import (
    SystemWalletsAggregationConfig,
)
from app.scripe.application.services.SystemWalletProvisioningService import (
    SystemWalletProvisioningService,
)


class SystemWalletsAggregationVirtualManyToOneOperation:
    IDEMPOTENCY_PREFIX = "system_wallets_aggregation:virtual"
    DESCRIPTION_PREFIX = "System wallets aggregation"

    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        execution_time: datetime,
        source_wallet_code: str,
        destination_wallet_code: str,
        target_balance_minor: int,
    ) -> dict[str, int]:
        if execution_time.tzinfo is None:
            raise ValueError("Execution time must be timezone-aware.")
        if (
            isinstance(target_balance_minor, bool)
            or not isinstance(target_balance_minor, int)
        ):
            raise ValueError("Target balance must be an integer.")
        if target_balance_minor < 0:
            raise ValueError("Target balance must not be negative.")

        SystemWalletsAggregationConfig.validate()
        expected_pair = SystemWalletsAggregationConfig.get_wallet_pair(
            source_wallet_code
        )
        if expected_pair[1] != destination_wallet_code:
            raise ValueError(
                f"Invalid aggregation wallet pair: "
                f"{source_wallet_code} -> {destination_wallet_code}."
            )

        config = SystemWalletsAggregationConfig
        hour_key = execution_time.astimezone(timezone.utc).strftime(
            "%Y%m%dT%H"
        )
        idempotency_key = (
            f"{cls.IDEMPOTENCY_PREFIX}:"
            f"{destination_wallet_code}:{hour_key}"
        )

        with session.begin():
            accounts_by_code = (
                SystemFundsConsolidationWalletValidator.lock_required_wallets(
                    session,
                    (destination_wallet_code,),
                    currency_code=config.CURRENCY_CODE,
                )
            )
            existing = session.execute(
                select(Transaction).where(
                    Transaction.idempotency_key == idempotency_key,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return {
                    "amount_minor": 0,
                    "created": 0,
                    "total_minor": target_balance_minor,
                    "delta_minor": 0,
                }

            destination: Account = accounts_by_code[destination_wallet_code]
            previous_destination_balance = account_posted_balance_minor(
                session,
                destination.id,
            )
            delta_minor = target_balance_minor - previous_destination_balance
            if delta_minor == 0:
                return {
                    "amount_minor": 0,
                    "created": 0,
                    "total_minor": target_balance_minor,
                    "delta_minor": 0,
                }

            adjustment_direction = (
                LedgerEntryDirection.CREDIT
                if delta_minor >= 0
                else LedgerEntryDirection.DEBIT
            )
            adjustment_amount = abs(delta_minor)

            transaction_id = uuid4()
            transaction = Transaction(
                id=transaction_id,
                type=TransactionType.VIRTUAL_CONSOLIDATION,
                status=TransactionStatus.POSTED,
                currency_code=config.CURRENCY_CODE,
                idempotency_key=idempotency_key,
                description=(
                    f"{cls.DESCRIPTION_PREFIX} "
                    f"{source_wallet_code} -> {destination_wallet_code} "
                    f"{hour_key}"
                ),
            )
            session.add(transaction)
            session.flush()

            session.add(
                LedgerEntry(
                    tx_id=transaction_id,
                    account_id=destination.id,
                    currency_code=config.CURRENCY_CODE,
                    direction=adjustment_direction,
                    amount=adjustment_amount,
                )
            )
            write_audit_event(
                session,
                event_type="system_wallets_aggregation_virtual",
                entity_type="transaction",
                entity_id=str(transaction_id),
                payload_json={
                    "source_wallet_code": source_wallet_code,
                    "destination_wallet_code": destination_wallet_code,
                    "previous_destination_balance_minor": (
                        previous_destination_balance
                    ),
                    "target_balance_minor": target_balance_minor,
                    "delta_minor": delta_minor,
                    "adjustment_direction": adjustment_direction.value,
                    "amount_minor": adjustment_amount,
                    "currency_code": config.CURRENCY_CODE,
                    "execution_hour": hour_key,
                    "virtual": True,
                    "source_debits_created": False,
                    "system_owner_id": str(
                        SystemWalletProvisioningService.SYSTEM_OWNER_ID
                    ),
                },
            )

        return {
            "amount_minor": adjustment_amount,
            "created": 1,
            "total_minor": target_balance_minor,
            "delta_minor": delta_minor,
        }
