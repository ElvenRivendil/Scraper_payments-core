# /* ../NauTrader_Helm/payments-core/tests/scripe/application/services/integration/test_scripe_wallet_transfer_integration.py */
from app.models.enums import LedgerEntryDirection, TransactionType
from app.models.ledger_entry import LedgerEntry
from app.models.transaction import Transaction
from app.scripe.application.services.ScripeDepositService import ScripeDepositService
from app.scripe.application.services.ScripeWalletTransferService import ScripeWalletTransferService


class TestScripeWalletTransferIntegration:
    def test_transfer_moves_scr_between_owned_wallets(self, app, scripe_wallet_context) -> None:
        context = scripe_wallet_context
        with app.state.session_factory() as session:
            ScripeDepositService().deposit(
                session,
                owner_id=context["owner_id"],
                amount_minor=2000,
                idempotency_key="test-scripe-transfer-fund-001",
            )
            ScripeWalletTransferService().transfer(
                session,
                owner_id=context["owner_id"],
                from_account_id=context["wallets"]["PM"],
                to_account_id=context["wallets"]["ER"],
                amount_minor=650,
                idempotency_key="test-scripe-transfer-001",
                description="Integration test transfer",
            )
            transaction = session.query(Transaction).filter(
                Transaction.idempotency_key == "test-scripe-transfer-001"
            ).one()
            entries = session.query(LedgerEntry).filter(
                LedgerEntry.tx_id == transaction.id
            ).all()
            entries_by_direction = {entry.direction: entry for entry in entries}

            assert transaction.type == TransactionType.TRANSFER
            assert transaction.currency_code == "SCR"
            assert len(entries) == 2
            assert entries_by_direction[LedgerEntryDirection.DEBIT].account_id == context["wallets"]["PM"]
            assert entries_by_direction[LedgerEntryDirection.CREDIT].account_id == context["wallets"]["ER"]
            assert all(entry.amount == 650 for entry in entries)
            assert all(entry.currency_code == "SCR" for entry in entries)
