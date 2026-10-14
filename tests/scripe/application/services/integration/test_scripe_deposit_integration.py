# /* ../NauTrader_Helm/payments-core/tests/scripe/application/services/integration/test_scripe_deposit_integration.py */
from app.models.enums import LedgerEntryDirection
from app.models.ledger_entry import LedgerEntry
from app.models.transaction import Transaction
from app.scripe.application.services.ScripeDepositService import ScripeDepositService


class TestScripeDepositIntegration:
    def test_deposit_credits_owned_scr_pm_wallet(self, app, scripe_wallet_context) -> None:
        context = scripe_wallet_context
        with app.state.session_factory() as session:
            transaction = ScripeDepositService().deposit(
                session,
                owner_id=context["owner_id"],
                amount_minor=1250,
                idempotency_key="test-scripe-deposit-001",
            )
            entry = session.query(LedgerEntry).filter(
                LedgerEntry.tx_id == transaction.id
            ).one()
            stored_transaction = session.get(Transaction, transaction.id)

            assert stored_transaction is not None
            assert stored_transaction.description == "Scripe deposit"
            assert stored_transaction.currency_code == "SCR"
            assert entry.account_id == context["wallets"]["PM"]
            assert entry.currency_code == "SCR"
            assert entry.direction == LedgerEntryDirection.CREDIT
            assert entry.amount == 1250

    def test_repeated_deposit_is_idempotent(self, app, scripe_wallet_context) -> None:
        context = scripe_wallet_context
        with app.state.session_factory() as session:
            service = ScripeDepositService()
            first = service.deposit(
                session,
                owner_id=context["owner_id"],
                amount_minor=500,
                idempotency_key="test-scripe-deposit-replay-001",
            )
            second = service.deposit(
                session,
                owner_id=context["owner_id"],
                amount_minor=500,
                idempotency_key="test-scripe-deposit-replay-001",
            )
            entries = session.query(LedgerEntry).filter(
                LedgerEntry.tx_id == first.id
            ).all()

            assert first.id == second.id
            assert len(entries) == 1
