# /* ../NauTrader_Helm/payments-core/tests/scripe/application/services/integration/test_demo_reset_safety_integration.py */
from __future__ import annotations
from datetime import UTC, datetime, timedelta
from uuid import UUID
import pytest
from sqlalchemy import select
from app.models import Account, Hold, LedgerEntry, Transaction
from app.models.enums import HoldStatus, LedgerEntryDirection, TransactionStatus, TransactionType
from app.services.demo_reset import DemoResetUnsafeError, reset_demo_data_safely
class TestDemoResetSafetyIntegration:
    def _mark_demo_accounts(self, session) -> set[UUID]:
        accounts = list(session.execute(select(Account)).scalars())
        demo_accounts = [
            account
            for account in accounts
            if account.owner_id == UUID(int=1)
            and account.name.split(" ", 1)[0] in {"INR", "USD", "EUR"}
            and account.name.split(" ", 1)[1]
            in {"Mint Source", "Treasury", "Alice Wallet", "Corner Shop", "Escrow"}
        ]
        for account in demo_accounts:
            account.is_demo = True
            account.owner_id = None
        session.flush()
        return {account.id for account in demo_accounts}
    def _add_external_account(self, session) -> Account:
        account = Account(
            owner_id=UUID(int=999),
            name="INR Real User Wallet",
            currency_code="INR",
            type=next(
                item.type
                for item in session.execute(select(Account)).scalars()
                if item.name == "INR Alice Wallet"
            ),
            is_demo=False,
            is_system=False,
        )
        session.add(account)
        session.flush()
        return account
    def _add_transaction(self, session, account: Account, key: str) -> Transaction:
        transaction = Transaction(
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.POSTED,
            currency_code="INR",
            idempotency_key=key,
            description="Safety test transaction",
        )
        session.add(transaction)
        session.flush()
        session.add(
            LedgerEntry(
                tx_id=transaction.id,
                account_id=account.id,
                currency_code="INR",
                direction=LedgerEntryDirection.CREDIT,
                amount=100,
            )
        )
        session.flush()
        return transaction
    def test_rejects_demo_transaction_linked_to_external_account(self, app) -> None:
        with app.state.session_factory() as session:
            demo_ids = self._mark_demo_accounts(session)
            external = self._add_external_account(session)
            transaction = self._add_transaction(session, external, "test-demo-reset-external-ledger")
            demo_account = session.execute(
                select(Account).where(Account.name == "INR Alice Wallet")
            ).scalar_one()
            session.add(
                LedgerEntry(
                    tx_id=transaction.id,
                    account_id=demo_account.id,
                    currency_code="INR",
                    direction=LedgerEntryDirection.DEBIT,
                    amount=100,
                )
            )
            session.commit()
            before_entries = session.execute(select(LedgerEntry.id)).scalars().all()
            with pytest.raises(DemoResetUnsafeError):
                reset_demo_data_safely(session)
            assert session.execute(select(LedgerEntry.id)).scalars().all() == before_entries
            assert session.get(Account, external.id) is not None
            assert demo_ids.issubset(
                set(session.execute(select(Account.id).where(Account.is_demo.is_(True))).scalars())
            )
    def test_rejects_external_hold_capturing_demo_transaction(self, app) -> None:
        with app.state.session_factory() as session:
            self._mark_demo_accounts(session)
            external = self._add_external_account(session)
            demo_account = session.execute(
                select(Account).where(Account.name == "INR Alice Wallet")
            ).scalar_one()
            transaction = self._add_transaction(session, demo_account, "test-demo-reset-external-hold")
            hold = Hold(
                account_id=external.id,
                currency_code="INR",
                amount=100,
                status=HoldStatus.AUTHORIZED,
                expires_at=datetime.now(UTC) + timedelta(days=1),
                captured_tx_id=transaction.id,
            )
            session.add(hold)
            session.commit()
            before_transactions = session.execute(select(Transaction.id)).scalars().all()
            before_entries = session.execute(select(LedgerEntry.id)).scalars().all()
            with pytest.raises(DemoResetUnsafeError):
                reset_demo_data_safely(session)
            assert session.execute(select(Transaction.id)).scalars().all() == before_transactions
            assert session.execute(select(LedgerEntry.id)).scalars().all() == before_entries
            assert session.get(Hold, hold.id) is not None

    def test_rejects_additional_demo_transaction_without_changes(self, app) -> None:
        with app.state.session_factory() as session:
            self._mark_demo_accounts(session)
            demo_account = session.execute(
                select(Account).where(Account.name == "INR Alice Wallet")
            ).scalar_one()
            self._add_transaction(session, demo_account, "user-demo-transaction")
            session.commit()
            before_transactions = set(session.execute(select(Transaction.id)).scalars())
            before_entries = set(session.execute(select(LedgerEntry.id)).scalars())

            with pytest.raises(DemoResetUnsafeError):
                reset_demo_data_safely(session)

            assert set(session.execute(select(Transaction.id)).scalars()) == before_transactions
            assert set(session.execute(select(LedgerEntry.id)).scalars()) == before_entries

    def test_rejects_hold_attached_to_demo_account_without_changes(self, app) -> None:
        with app.state.session_factory() as session:
            demo_ids = self._mark_demo_accounts(session)
            demo_account = session.execute(
                select(Account).where(Account.name == "INR Alice Wallet")
            ).scalar_one()
            hold = Hold(
                account_id=demo_account.id,
                currency_code="INR",
                amount=900,
                status=HoldStatus.AUTHORIZED,
                expires_at=datetime.now(UTC) + timedelta(days=7),
            )
            session.add(hold)
            session.commit()
            before_transactions = session.execute(select(Transaction.id)).scalars().all()
            before_entries = session.execute(select(LedgerEntry.id)).scalars().all()
            before_holds = session.execute(select(Hold.id)).scalars().all()

            with pytest.raises(DemoResetUnsafeError):
                reset_demo_data_safely(session)

            assert session.execute(select(Transaction.id)).scalars().all() == before_transactions
            assert session.execute(select(LedgerEntry.id)).scalars().all() == before_entries
            assert session.execute(select(Hold.id)).scalars().all() == before_holds
            assert session.get(Hold, hold.id) is not None
            assert demo_ids.issubset(
                set(session.execute(select(Account.id).where(Account.is_demo.is_(True))).scalars())
            )
