# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/application/operations/VirtualManyToOneOperation.py */
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, LedgerEntry, Transaction
from app.models.enums import LedgerEntryDirection, TransactionStatus, TransactionType
from app.services.audit import write_audit_event
from app.services.balances import (
    account_balances_minor,
    account_posted_balance_minor,
)
from app.services.SystemFundsConsolidation.application.services.SystemFundsConsolidationWalletValidator import (
    SystemFundsConsolidationWalletValidator,
)
from app.services.SystemFundsConsolidation.domain.config.VirtualManyToOneConfig import (
    VirtualManyToOneConfig,
)
from app.scripe.application.services.SystemWalletProvisioningService import (
    SystemWalletProvisioningService,
)


class VirtualManyToOneOperation:
    @classmethod
    def execute(cls, session: Session, *, execution_time: datetime) -> dict[str, int]:
        if execution_time.tzinfo is None:
            raise ValueError("Execution time must be timezone-aware.")

        config = VirtualManyToOneConfig
        config.validate()
        hour_key = execution_time.astimezone(timezone.utc).strftime("%Y%m%dT%H")
        idempotency_key = (
            f"{config.IDEMPOTENCY_PREFIX}:virtual:"
            f"{config.DESTINATION_WALLET_CODE}:{hour_key}"
        )
        required_codes = (
            *config.SOURCE_WALLET_CODES,
            config.DESTINATION_WALLET_CODE,
        )

        with session.begin():
            accounts_by_code = SystemFundsConsolidationWalletValidator.lock_required_wallets(
                session,
                required_codes,
                currency_code=config.CURRENCY_CODE,
            )
            existing = session.execute(
                select(Transaction).where(
                    Transaction.idempotency_key == idempotency_key,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return {"amount_minor": 0, "created": 0}

            destination: Account = accounts_by_code[config.DESTINATION_WALLET_CODE]
            total_source_available = 0
            source_amounts: dict[str, int] = {}

            for source_code in config.SOURCE_WALLET_CODES:
                source: Account = accounts_by_code[source_code]
                _posted, _held, available = account_balances_minor(session, source.id)
                amount = max(0, available)
                source_amounts[source_code] = amount
                total_source_available += amount

            previous_destination_balance = account_posted_balance_minor(
                session,
                destination.id,
            )
            delta_minor = total_source_available - previous_destination_balance
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
                    f"{config.DESCRIPTION_PREFIX} "
                    f"VIRTUAL_MANY_TO_ONE {hour_key}"
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
                event_type="system_funds_virtual_consolidation",
                entity_type="transaction",
                entity_id=str(transaction_id),
                payload_json={
                    "execution_type": config.EXECUTION_TYPE,
                    "source_wallets": source_amounts,
                    "destination_wallet": config.DESTINATION_WALLET_CODE,
                    "previous_destination_balance_minor": previous_destination_balance,
                    "target_balance_minor": total_source_available,
                    "delta_minor": delta_minor,
                    "adjustment_direction": adjustment_direction.value,
                    "amount_minor": adjustment_amount,
                    "currency_code": config.CURRENCY_CODE,
                    "execution_hour": hour_key,
                    "virtual": True,
                    "source_debits_created": False,
                    "system_owner_id": str(SystemWalletProvisioningService.SYSTEM_OWNER_ID),
                },
            )

        return {
            "amount_minor": adjustment_amount,
            "created": 1,
            "total_minor": total_source_available,
            "delta_minor": delta_minor,
        }
