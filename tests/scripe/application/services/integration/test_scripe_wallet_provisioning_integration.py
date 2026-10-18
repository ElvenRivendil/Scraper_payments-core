# /* ../NauTrader_Helm/payments-core/tests/scripe/application/services/integration/test_scripe_wallet_provisioning_integration.py */
from uuid import UUID

from sqlalchemy import select

from app.models import Account
from app.scripe.application.services.ScripeCurrencyRegistrationService import (
    ScripeCurrencyRegistrationService,
)
from app.scripe.application.services.ScripeWalletProvisioningService import (
    ScripeWalletProvisioningService,
)


class TestScripeWalletProvisioningIntegration:
    def test_provisioning_creates_thirteen_wallets_and_is_idempotent(self, app) -> None:
        owner_id = UUID("12345678-1234-5678-1234-567812345678")

        with app.state.session_factory() as session:
            ScripeCurrencyRegistrationService.register(session)
            first_result = ScripeWalletProvisioningService.provision(session, owner_id)
            second_result = ScripeWalletProvisioningService.provision(session, owner_id)

            accounts = session.execute(
                select(Account).where(Account.owner_id == owner_id)
            ).scalars().all()

        expected_codes = [
            "ER", "IS", "PM", "BD", "SYA", "ITF", "EWF",
            "OCF", "PCF", "PTC", "DPA", "ILA", "RVA",
        ]
        assert [wallet["wallet_code"] for wallet in first_result] == expected_codes
        assert [wallet["wallet_code"] for wallet in second_result] == expected_codes
        assert [wallet["id"] for wallet in first_result] == [
            wallet["id"] for wallet in second_result
        ]
        assert len(accounts) == 13
        assert len({account.wallet_code for account in accounts}) == 13
        assert all(wallet["currency_code"] == "SCR" for wallet in first_result)
