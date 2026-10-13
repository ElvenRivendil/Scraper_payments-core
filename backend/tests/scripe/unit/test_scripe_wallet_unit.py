# /* payments-core/backend/tests/scripe/unit/test_scripe_wallet_unit.py */
from app.scripe.domain.entities.ScripeWallet import ScripeWallet


def test_standard_scripe_wallets_have_expected_codes_and_order() -> None:
    wallets = ScripeWallet.standard_wallets()

    assert [wallet.code for wallet in wallets] == ["ER", "IS", "PM", "BD"]
    assert [wallet.name for wallet in wallets] == [
        "Emergency Reserve",
        "Investment Savings",
        "Pocket Money",
        "Bonus Department",
    ]
    assert [wallet.position for wallet in wallets] == [1, 2, 3, 4]
