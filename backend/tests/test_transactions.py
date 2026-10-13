# /* ../NauTrader_Helm/payments-core/backend/tests/test_transactions.py */
from uuid import UUID

from app.core.auth import AuthenticatedUser, require_current_user


def _create_transaction(client, idempotency_key: str) -> str:
    accounts = client.get("/accounts").json()
    source = next(account for account in accounts if account["name"] == "INR Alice Wallet")
    destination = next(account for account in accounts if account["name"] == "INR Corner Shop")
    response = client.post(
        "/transfers",
        json={
            "from_account_id": source["id"],
            "to_account_id": destination["id"],
            "currency_code": "INR",
            "amount_minor": 100,
            "description": "Transaction ownership test",
        },
        headers={"Idempotency-Key": idempotency_key},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_transaction_list_excludes_another_users_transaction(client):
    transaction_id = _create_transaction(client, "transaction-owner-list-001")
    original_override = client.app.dependency_overrides[require_current_user]
    client.app.dependency_overrides[require_current_user] = (
        lambda: AuthenticatedUser(id=UUID(int=2))
    )
    try:
        response = client.get("/transactions")
    finally:
        client.app.dependency_overrides[require_current_user] = original_override

    assert response.status_code == 200
    assert transaction_id not in {item["id"] for item in response.json()}


def test_transaction_detail_rejects_another_users_transaction(client):
    transaction_id = _create_transaction(client, "transaction-owner-detail-001")
    original_override = client.app.dependency_overrides[require_current_user]
    client.app.dependency_overrides[require_current_user] = (
        lambda: AuthenticatedUser(id=UUID(int=2))
    )
    try:
        response = client.get(f"/transactions/{transaction_id}")
    finally:
        client.app.dependency_overrides[require_current_user] = original_override

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"
