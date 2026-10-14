# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/services/ScripeTestResetService.py */
from uuid import UUID

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import LedgerEntryDirection, TransactionStatus
from app.models.ledger_entry import LedgerEntry
from app.models.transaction import Transaction
from app.scripe.application.services.ScripeLedgerAdjustmentService import ScripeLedgerAdjustmentService


class ScripeTestResetService:
    def __init__(self) -> None:
        self.adjustments = ScripeLedgerAdjustmentService()

    def reset(
        self,
        session: Session,
        *,
        owner_id: UUID,
        idempotency_key: str,
    ) -> Transaction:
        account = (
            session.query(Account)
            .filter(
                Account.owner_id == owner_id,
                Account.wallet_code == "PM",
                Account.currency_code == "SCR",
            )
            .with_for_update()
            .one_or_none()
        )
        if account is None:
            raise ValueError("The owner's SCR PM wallet was not found")

        existing = (
            session.query(Transaction)
            .filter(Transaction.idempotency_key == idempotency_key)
            .one_or_none()
        )
        if existing is not None:
            entries = (
                session.query(LedgerEntry)
                .filter(LedgerEntry.tx_id == existing.id)
                .all()
            )
            if (
                existing.description == "Test reset"
                and existing.currency_code == "SCR"
                and len(entries) == 1
                and entries[0].account_id == account.id
                and entries[0].direction == LedgerEntryDirection.DEBIT
            ):
                return existing
            raise ValueError("Idempotency key was already used for another operation")

        balance = (
            session.query(
                func.coalesce(
                    func.sum(
                        LedgerEntry.amount
                        * case(
                            (LedgerEntry.direction == LedgerEntryDirection.CREDIT, 1),
                            else_=-1,
                        )
                    ),
                    0,
                )
            )
            .join(Transaction, Transaction.id == LedgerEntry.tx_id)
            .filter(
                LedgerEntry.account_id == account.id,
                Transaction.status == TransactionStatus.POSTED,
            )
            .scalar()
        )
        balance_minor = int(balance or 0)
        if balance_minor <= 0:
            raise ValueError("The SCR PM wallet has no positive balance to reset")

        return self.adjustments.create_adjustment(
            session,
            account=account,
            amount_minor=balance_minor,
            description="Test reset",
            idempotency_key=idempotency_key,
        )
