# /* ../NauTrader_Helm/payments-core/tests/services/UserFundsCollection/domain/config/unit/user_funds_collection_config_unit.py */

import pytest

from app.services.UserFundsCollection.domain.config.UserFundsCollectionConfig import (
    UserFundsCollectionConfig,
)


def test_config_contains_seven_confirmed_wallet_pairs():
    assert UserFundsCollectionConfig.get_wallet_pairs() == (
        ("ITF", "ITFP"),
        ("EWF", "EWFP"),
        ("OCF", "OCFP"),
        ("PCF", "PCFP"),
        ("PTC", "PTCP"),
        ("DPA", "DPAP"),
        ("ILA", "ILAP"),
    )


def test_config_uses_scr_currency():
    assert UserFundsCollectionConfig.CURRENCY_CODE == "SCR"


def test_config_validation_succeeds():
    UserFundsCollectionConfig.validate()


def test_config_rejects_duplicate_user_wallet_codes(monkeypatch):
    monkeypatch.setattr(
        UserFundsCollectionConfig,
        "WALLET_PAIRS",
        (("ITF", "ITFP"), ("ITF", "EWF")),
    )

    with pytest.raises(ValueError, match="User wallet codes must be unique"):
        UserFundsCollectionConfig.validate()


def test_config_rejects_duplicate_system_wallet_codes(monkeypatch):
    monkeypatch.setattr(
        UserFundsCollectionConfig,
        "WALLET_PAIRS",
        (("ITF", "ITFP"), ("EWF", "ITFP")),
    )

    with pytest.raises(ValueError, match="System wallet codes must be unique"):
        UserFundsCollectionConfig.validate()
