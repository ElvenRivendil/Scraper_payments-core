# /* ../NauTrader_Helm/payments-core/backend/alembic/versions/0008_demo_account_marker.py */
from uuid import UUID

from alembic import op
import sqlalchemy as sa


revision = "0008_demo_account_marker"
down_revision = "0007_system_wallet_accounts"
branch_labels = None
depends_on = None


CURRENCIES = ("EUR", "INR", "USD")
SUFFIX_TYPES = {
    "Mint Source": "MERCHANT",
    "Treasury": "MERCHANT",
    "Alice Wallet": "USER",
    "Corner Shop": "MERCHANT",
    "Escrow": "ESCROW",
}
OPENING_AMOUNT = 500000
ZERO_UUID = UUID(int=0)


def _bind_list(prefix: str, values: tuple) -> tuple[str, dict]:
    names = [f"{prefix}_{index}" for index in range(len(values))]
    clause = ", ".join(f":{name}" for name in names)
    return clause, dict(zip(names, values))


def upgrade() -> None:
    connection = op.get_bind()
    expected_names = {
        f"{currency} {suffix}"
        for currency in CURRENCIES
        for suffix in SUFFIX_TYPES
    }
    names_clause, names_params = _bind_list("name", tuple(sorted(expected_names)))

    accounts = connection.execute(
        sa.text(
            "SELECT id, owner_id, name, currency_code, wallet_code, is_system, type "
            f"FROM accounts WHERE name IN ({names_clause})"
        ),
        names_params,
    ).mappings().all()

    if len(accounts) != 15 or {row["name"] for row in accounts} != expected_names:
        raise RuntimeError(
            "Demo marker migration aborted: expected exactly 15 known demo accounts."
        )

    accounts_by_name = {row["name"]: row for row in accounts}
    for currency in CURRENCIES:
        for suffix, expected_type in SUFFIX_TYPES.items():
            row = accounts_by_name[f"{currency} {suffix}"]
            if row["currency_code"] != currency or row["type"] != expected_type:
                raise RuntimeError(
                    f"Demo marker migration aborted: unexpected currency or type for {row['name']}."
                )
            if row["wallet_code"] is not None or row["is_system"]:
                raise RuntimeError(
                    f"Demo marker migration aborted: unsafe account flags for {row['name']}."
                )
            if row["owner_id"] not in (None, ZERO_UUID):
                raise RuntimeError(
                    f"Demo marker migration aborted: unexpected owner for {row['name']}."
                )

    account_ids = tuple(row["id"] for row in accounts)
    account_clause, account_params = _bind_list("account", account_ids)
    escrow_rows = connection.execute(
        sa.text(
            "SELECT ea.currency_code, a.name "
            "FROM escrow_accounts ea JOIN accounts a ON a.id = ea.account_id "
            f"WHERE a.id IN ({account_clause})"
        ),
        account_params,
    ).mappings().all()
    expected_escrows = {(currency, f"{currency} Escrow") for currency in CURRENCIES}
    if {(row["currency_code"], row["name"]) for row in escrow_rows} != expected_escrows:
        raise RuntimeError(
            "Demo marker migration aborted: escrow account mappings do not match the expected demo set."
        )

    opening_keys = tuple(f"seed:{currency}:opening" for currency in CURRENCIES)
    key_clause, key_params = _bind_list("key", opening_keys)
    transactions = connection.execute(
        sa.text(
            "SELECT id, idempotency_key, currency_code, type, status, description "
            f"FROM transactions WHERE idempotency_key IN ({key_clause})"
        ),
        key_params,
    ).mappings().all()
    if len(transactions) != 3 or {row["idempotency_key"] for row in transactions} != set(opening_keys):
        raise RuntimeError(
            "Demo marker migration aborted: expected exactly three opening transactions."
        )

    transactions_by_key = {row["idempotency_key"]: row for row in transactions}
    for currency in CURRENCIES:
        key = f"seed:{currency}:opening"
        transaction = transactions_by_key[key]
        if (
            transaction["currency_code"] != currency
            or transaction["type"] != "DEPOSIT"
            or transaction["status"] != "POSTED"
            or transaction["description"] != f"Opening balance for {currency} demo accounts"
        ):
            raise RuntimeError(
                f"Demo marker migration aborted: unexpected opening transaction for {currency}."
            )

    transaction_ids = tuple(row["id"] for row in transactions)
    tx_clause, tx_params = _bind_list("tx", transaction_ids)
    entries = connection.execute(
        sa.text(
            "SELECT le.tx_id, le.account_id, le.currency_code, le.direction, le.amount, a.name "
            "FROM ledger_entries le JOIN accounts a ON a.id = le.account_id "
            f"WHERE le.tx_id IN ({tx_clause})"
        ),
        tx_params,
    ).mappings().all()

    expected_entries = set()
    for currency in CURRENCIES:
        tx_id = transactions_by_key[f"seed:{currency}:opening"]["id"]
        expected_entries.add(
            (tx_id, accounts_by_name[f"{currency} Mint Source"]["id"], currency, "DEBIT", OPENING_AMOUNT)
        )
        expected_entries.add(
            (tx_id, accounts_by_name[f"{currency} Alice Wallet"]["id"], currency, "CREDIT", OPENING_AMOUNT)
        )

    actual_entries = {
        (row["tx_id"], row["account_id"], row["currency_code"], row["direction"], row["amount"])
        for row in entries
    }
    if len(entries) != 6 or actual_entries != expected_entries:
        raise RuntimeError(
            "Demo marker migration aborted: opening transaction ledger entries do not match the expected six entries."
        )

    demo_account_ids = set(account_ids)
    if any(row["account_id"] not in demo_account_ids for row in entries):
        raise RuntimeError(
            "Demo marker migration aborted: an opening transaction references a non-demo account."
        )

    account_tx_ids = connection.execute(
        sa.text(
            "SELECT DISTINCT tx_id FROM ledger_entries "
            f"WHERE account_id IN ({account_clause})"
        ),
        account_params,
    ).scalars().all()
    if set(account_tx_ids) != set(transaction_ids):
        raise RuntimeError(
            "Demo marker migration aborted: a known demo account has unexpected transaction history."
        )

    op.add_column(
        "accounts",
        sa.Column(
            "is_demo",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    id_clause, id_params = _bind_list("demo_id", account_ids)
    connection.execute(
        sa.text(f"UPDATE accounts SET is_demo = TRUE WHERE id IN ({id_clause})"),
        id_params,
    )


def downgrade() -> None:
    op.drop_column("accounts", "is_demo")
