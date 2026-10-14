# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/services/ScripeTestDepositService.py */
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.account import Account
from app.scripe.application.services.ScripeLedgerAdjustmentService import ScripeLedgerAdjustmentService


class ScripeTestDepositService:
    def __init__(self) -> None:
        self.adjustments = ScripeLedgerAdjustmentService()

    def deposit(
        self,
        session: Session,
        *,
        owner_id: UUID,
        amount_minor: int,
        idempotency_key: str,
    ):
        account = (
            session.query(Account)
            .filter(
                Account.owner_id == owner_id,
                Account.wallet_code == "PM",
                Account.currency_code == "SCR",
            )
            .one_or_none()
        )
        if account is None:
            raise ValueError("The owner's SCR PM wallet was not found")
        return self.adjustments.create_adjustment(
            session,
            account=account,
            amount_minor=amount_minor,
            description="Test deposit",
            idempotency_key=idempotency_key,
        )
