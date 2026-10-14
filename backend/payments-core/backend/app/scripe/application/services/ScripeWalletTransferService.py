# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/services/ScripeWalletTransferService.py */
from sqlalchemy.orm import Session
from app.models.account import Account
from app.schemas import TransferCreate
from app.services.transfers import create_transfer


class ScripeWalletTransferService:
    def transfer(
        self,
        session: Session,
        *,
        owner_id: int,
        from_account_id: int,
        to_account_id: int,
        amount_minor: int,
        idempotency_key: str,
        description: str | None = None,
    ):
        if from_account_id == to_account_id:
            raise ValueError("Source and destination wallets must be different")

        accounts = (
            session.query(Account)
            .filter(Account.id.in_([from_account_id, to_account_id]))
            .all()
        )
        accounts_by_id = {account.id: account for account in accounts}
        source = accounts_by_id.get(from_account_id)
        destination = accounts_by_id.get(to_account_id)

        if source is None or destination is None:
            raise ValueError("Source or destination wallet was not found")
        if source.owner_id != owner_id or destination.owner_id != owner_id:
            raise ValueError("Both wallets must belong to the authenticated owner")
        if source.currency_code != "SCR" or destination.currency_code != "SCR":
            raise ValueError("Only SCR wallet transfers are supported")
        if source.currency_code != destination.currency_code:
            raise ValueError("Wallet currencies must match")

        transfer = TransferCreate(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            currency_code="SCR",
            amount_minor=amount_minor,
            description=description,
        )
        return create_transfer(
            session,
            idempotency_key=idempotency_key,
            transfer=transfer,
            owner_id=owner_id,
        )
