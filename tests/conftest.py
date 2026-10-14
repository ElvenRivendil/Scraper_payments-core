# /* ../NauTrader_Helm/payments-core/tests/conftest.py */
from uuid import UUID

import pytest
from sqlalchemy import select

pytest_plugins = ("backend.tests.conftest",)

from app.models import Account
from app.scripe.application.services.ScripeCurrencyRegistrationService import (
    ScripeCurrencyRegistrationService,
)
from app.scripe.application.services.ScripeWalletProvisioningService import (
    ScripeWalletProvisioningService,
)


@pytest.fixture()
def scripe_wallet_context(app) -> dict:
    owner_id = UUID(int=999)
    with app.state.session_factory() as session:
        ScripeCurrencyRegistrationService.register(session)
        ScripeWalletProvisioningService.provision(session, owner_id)
        accounts = session.execute(
            select(Account).where(Account.owner_id == owner_id)
        ).scalars().all()
        wallets = {account.wallet_code: account.id for account in accounts}
    return {"owner_id": owner_id, "wallets": wallets}
