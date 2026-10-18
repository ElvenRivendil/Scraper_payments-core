# /* ../NauTrader_Helm/payments-core/tests/api/routes/end-to-end/test_account_wallet_visibility_end_to_end.py */
from uuid import UUID

import pytest

from app.core.auth import require_current_user
from app.scripe.application.services.ScripeCurrencyRegistrationService import (
    ScripeCurrencyRegistrationService,
)
from app.scripe.application.services.ScripeWalletProvisioningService import (
    ScripeWalletProvisioningService,
)
from support.RoleAuthenticatedTestUserDependency import (
    RoleAuthenticatedTestUserDependency,
)


class TestAccountWalletVisibilityEndToEnd:
    visible_codes = {"ER", "IS", "PM", "BD"}
    hidden_code = "SYA"
    privileged_roles = {"ADMINISTRATOR", "SUPER_ADMIN"}
    all_roles = [
        "USER",
        "ANONYMOUS",
        "MODERATOR",
        "ADMINISTRATOR",
        "SUPER_ADMIN",
    ]

    @staticmethod
    def _provision_wallets(app) -> dict[str, UUID]:
        owner_id = UUID(int=1)
        with app.state.session_factory() as session:
            ScripeCurrencyRegistrationService.register(session)
            ScripeWalletProvisioningService.provision(session, owner_id)
            from app.models import Account
            from sqlalchemy import select

            accounts = session.execute(
                select(Account).where(
                    Account.owner_id == owner_id,
                    Account.wallet_code.is_not(None),
                )
            ).scalars().all()
        return {account.wallet_code: account.id for account in accounts}

    @pytest.mark.parametrize("role", all_roles)
    def test_account_list_obeys_effective_role(self, client, app, role: str) -> None:
        self._provision_wallets(app)
        app.dependency_overrides[require_current_user] = (
            RoleAuthenticatedTestUserDependency(role)
        )

        response = client.get("/accounts")

        assert response.status_code == 200
        codes = {
            account["wallet_code"]
            for account in response.json()
            if account.get("wallet_code")
        }
        if role in self.privileged_roles:
            assert codes == self.visible_codes | {
                "SYA", "ITF", "EWF", "OCF", "PCF", "PTC", "DPA", "ILA", "RVA",
            }
        else:
            assert codes == self.visible_codes

    @pytest.mark.parametrize("role", all_roles)
    def test_hidden_wallet_detail_and_statement_obey_effective_role(
        self, client, app, role: str
    ) -> None:
        wallet_ids = self._provision_wallets(app)
        app.dependency_overrides[require_current_user] = (
            RoleAuthenticatedTestUserDependency(role)
        )
        wallet_id = wallet_ids[self.hidden_code]

        detail_response = client.get(f"/accounts/{wallet_id}")
        statement_response = client.get(f"/accounts/{wallet_id}/statement")

        expected_status = 200 if role in self.privileged_roles else 404
        assert detail_response.status_code == expected_status
        assert statement_response.status_code == expected_status
