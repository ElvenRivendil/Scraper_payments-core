# /* payments-core/backend/tests/scripe/integration/test_scripe_wallet_provisioning_integration.py */
from uuid import UUID

from app.scripe.application.services.ScripeWalletProvisioningService import (
    ScripeWalletProvisioningService,
)


def test_scripe_wallet_provisioning_is_ordered_and_idempotent(client) -> None:
    owner_id = UUID("12345678-1234-5678-1234-567812345678")

    with client.app.state.session_factory() as session:
        first_result = ScripeWalletProvisioningService.provision(session, owner_id)
        second_result = ScripeWalletProvisioningService.provision(session, owner_id)

    assert [wallet["wallet_code"] for wallet in first_result] == ["ER", "IS", "PM", "BD"]
    assert [wallet["wallet_code"] for wallet in second_result] == ["ER", "IS", "PM", "BD"]
    assert [wallet["id"] for wallet in first_result] == [
        wallet["id"] for wallet in second_result
    ]
    assert all(wallet["currency_code"] == "SCR" for wallet in first_result)
