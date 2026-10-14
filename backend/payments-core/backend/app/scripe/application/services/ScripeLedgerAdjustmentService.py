# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/services/ScripeLedgerAdjustmentService.py */
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.enums import LedgerEntryDirection, TransactionStatus, TransactionType
from app.models.ledger_entry import LedgerEntry
from app.models.transaction import Transaction


class ScripeLedgerAdjustmentService:
    CURRENCY_CODE = "SCR"
    POCKET_MONEY_CODE = "PM"
    DESCRIPTIONS = {
        "Scripe deposit": LedgerEntryDirection.CREDIT,
        "Test deposit": LedgerEntryDirection.CREDIT,
        "Test reset": LedgerEntryDirection.DEBIT,
    }

    def create_adjustment(
        self,
        session: Session,
        *,
        account: Account,
        amount_minor: int,
        description: str,
        idempotency_key: str,
    ) -> Transaction:
        if description not in self.DESCRIPTIONS:
            raise ValueError("Unsupported SCR adjustment description")
        if amount_minor <= 0:
            raise ValueError("Adjustment amount must be positive")
        if account.wallet_code != self.POCKET_MONEY_CODE:
            raise ValueError("SCR adjustments are allowed only for the PM wallet")
        if account.currency_code != self.CURRENCY_CODE:
            raise ValueError("SCR adjustments require an SCR account")
        if account.owner_id is None:
            raise ValueError("The PM wallet must have an owner")

        direction = self.DESCRIPTIONS[description]
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
                existing.type != TransactionType.DEPOSIT
                or existing.currency_code != self.CURRENCY_CODE
                or existing.description != description
                or len(entries) != 1
                or entries[0].account_id != account.id
                or entries[0].direction != direction
                or entries[0].amount != amount_minor
            ):
                raise ValueError("Idempotency key was already used for another operation")
            return existing

        transaction = Transaction(
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.POSTED,
            currency_code=self.CURRENCY_CODE,
            description=description,
            idempotency_key=idempotency_key,
        )
        session.add(transaction)
        session.flush()

        session.add(
            LedgerEntry(
                tx_id=transaction.id,
                account_id=account.id,
                currency_code=self.CURRENCY_CODE,
                direction=direction,
                amount=amount_minor,
            )
        )
        session.commit()
        session.refresh(transaction)
        return transaction
