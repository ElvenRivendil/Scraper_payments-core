# /* ../NauTrader_Helm/payments-core/tests/scripe/application/services/integration/test_scripe_test_deposit_integration.py */
from app.models.enums import LedgerEntryDirection
from app.models.ledger_entry import LedgerEntry
from app.scripe.application.services.ScripeTestDepositService import (
    ScripeTestDepositService,
)


class TestScripeTestDepositIntegration:
    def test_test_deposit_credits_pm_without_source_account(
        self, app, scripe_wallet_context
    ) -> None:
        context = scripe_wallet_context
        with app.state.session_factory() as session:
            transaction = ScripeTestDepositService().deposit(
                session,
                owner_id=context["owner_id"],
                amount_minor=700,
                idempotency_key="test-scripe-test-deposit-001",
            )
            entries = session.query(LedgerEntry).filter(
                LedgerEntry.tx_id == transaction.id
            ).all()

            assert len(entries) == 1
            assert entries[0].account_id == context["wallets"]["PM"]
            assert entries[0].currency_code == "SCR"
            assert entries[0].direction == LedgerEntryDirection.CREDIT
            assert entries[0].amount == 700
            assert transaction.description == "Test deposit"
