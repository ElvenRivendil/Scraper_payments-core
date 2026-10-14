# /* ../NauTrader_Helm/payments-core/tests/scripe/application/services/integration/test_scripe_test_reset_integration.py */
import pytest

from app.models.enums import LedgerEntryDirection
from app.models.ledger_entry import LedgerEntry
from app.scripe.application.services.ScripeDepositService import ScripeDepositService
from app.scripe.application.services.ScripeTestResetService import ScripeTestResetService


class TestScripeTestResetIntegration:
    def test_reset_debits_entire_pm_balance(self, app, scripe_wallet_context) -> None:
        context = scripe_wallet_context
        with app.state.session_factory() as session:
            ScripeDepositService().deposit(
                session,
                owner_id=context["owner_id"],
                amount_minor=1800,
                idempotency_key="test-scripe-reset-fund-001",
            )
            transaction = ScripeTestResetService().reset(
                session,
                owner_id=context["owner_id"],
                idempotency_key="test-scripe-reset-001",
            )
            entries = session.query(LedgerEntry).filter(
                LedgerEntry.tx_id == transaction.id
            ).all()

            assert transaction.description == "Test reset"
            assert len(entries) == 1
            assert entries[0].account_id == context["wallets"]["PM"]
            assert entries[0].direction == LedgerEntryDirection.DEBIT
            assert entries[0].amount == 1800

    def test_reset_rejects_empty_pm_balance(self, app, scripe_wallet_context) -> None:
        context = scripe_wallet_context
        with app.state.session_factory() as session:
            with pytest.raises(ValueError, match="no positive balance"):
                ScripeTestResetService().reset(
                    session,
                    owner_id=context["owner_id"],
                    idempotency_key="test-scripe-reset-empty-001",
                )
