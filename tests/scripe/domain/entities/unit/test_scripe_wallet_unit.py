# /* ../NauTrader_Helm/payments-core/tests/scripe/domain/entities/unit/test_scripe_wallet_unit.py */
from app.scripe.domain.entities.ScripeWallet import ScripeWallet


class TestScripeWalletUnit:
    def test_standard_wallet_catalog_contains_all_thirteen_wallets(self) -> None:
        wallets = ScripeWallet.standard_wallets()

        assert [wallet.code for wallet in wallets] == [
            "ER", "IS", "PM", "BD", "SYA", "ITF", "EWF",
            "OCF", "PCF", "PTC", "DPA", "ILA", "RVA",
        ]
        assert [wallet.position for wallet in wallets] == list(range(1, 14))
        assert [wallet.name for wallet in wallets] == [
            "Emergency Reserve",
            "Investment Savings",
            "Pocket Money",
            "Bonus Department",
            "Staking Yield Account",
            "Internal Transfer Fee Account",
            "ER Deposit & Withdrawal Fee Account",
            "Order Open & Close Fee Account",
            "Position Open & Close Fee Account",
            "Profit Trade Commission Account",
            "Discount Plan Payment Account",
            "Identity Ledger Payment Account",
            "Reserve Account",
        ]
