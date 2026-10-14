# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/services/ScripeTestResetService.py */
from sqlalchemy import func
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
        owner_id: int,
        idempotency_key: str,
    ):
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

        balance = (
            session.query(
                func.coalesce(
                    func.sum(
                        LedgerEntry.amount
                        * func.case(
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
