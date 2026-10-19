# /* ../NauTrader_Helm/payments-core/tests/api/routes/end-to-end/test_system_wallet_access_end_to_end.py */
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.auth import require_current_user
from app.models import Account
from app.scripe.application.services.SystemWalletProvisioningService import SystemWalletProvisioningService
from support.RoleAuthenticatedTestUserDependency import RoleAuthenticatedTestUserDependency


class TestSystemWalletAccessEndToEnd:
    denied_roles = ["USER", "ANONYMOUS", "MODERATOR", "ADMINISTRATOR"]

    @staticmethod
    def _provision_system_wallets(app) -> dict[str, UUID]:
        with app.state.session_factory() as session:
            accounts = SystemWalletProvisioningService().provision(session)
            return {account.wallet_code: account.id for account in accounts}

    @staticmethod
    def _set_role(app, role: str) -> None:
        app.dependency_overrides[require_current_user] = (
            RoleAuthenticatedTestUserDependency(role)
        )

    def test_super_admin_can_list_all_system_wallets(self, client, app) -> None:
        self._provision_system_wallets(app)
        self._set_role(app, "SUPER_ADMIN")

        response = client.get("/admin/system-wallets")

        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) == 25
        assert {account["currency_code"] for account in accounts} == {"SCR"}
        assert {account["wallet_code"] for account in accounts} >= {"ERP", "PMP", "WRAP"}

    @pytest.mark.parametrize("role", denied_roles)
    def test_non_super_admin_cannot_list_system_wallets(
        self, client, app, role: str
    ) -> None:
        self._provision_system_wallets(app)
        self._set_role(app, role)

        response = client.get("/admin/system-wallets")

        assert response.status_code == 403

    def test_super_admin_can_read_system_wallet_detail_and_statement(
        self, client, app
    ) -> None:
        wallet_ids = self._provision_system_wallets(app)
        self._set_role(app, "SUPER_ADMIN")
        account_id = wallet_ids["ERP"]

        detail_response = client.get(f"/admin/system-wallets/{account_id}")
        statement_response = client.get(
            f"/admin/system-wallets/{account_id}/statement"
        )

        assert detail_response.status_code == 200
        assert detail_response.json()["wallet_code"] == "ERP"
        assert statement_response.status_code == 200
        assert statement_response.json()["account"]["wallet_code"] == "ERP"
        assert statement_response.json()["ledger_entries"] == []

    @pytest.mark.parametrize("role", denied_roles)
    def test_non_super_admin_cannot_read_detail_or_statement(
        self, client, app, role: str
    ) -> None:
        wallet_ids = self._provision_system_wallets(app)
        self._set_role(app, role)
        account_id = wallet_ids["ERP"]

        detail_response = client.get(f"/admin/system-wallets/{account_id}")
        statement_response = client.get(
            f"/admin/system-wallets/{account_id}/statement"
        )

        assert detail_response.status_code == 403
        assert statement_response.status_code == 403

    def test_regular_account_list_does_not_expose_system_wallets(
        self, client, app
    ) -> None:
        self._provision_system_wallets(app)
        self._set_role(app, "SUPER_ADMIN")

        response = client.get("/accounts")

        assert response.status_code == 200
        system_wallet_codes = {
            code for code, _name in SystemWalletProvisioningService.SYSTEM_WALLETS
        }
        assert all(
            account["wallet_code"] not in system_wallet_codes
            for account in response.json()
            if account.get("wallet_code")
        )
