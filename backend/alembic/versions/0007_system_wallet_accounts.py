# /* payments-core/backend/alembic/versions/0007_system_wallet_accounts.py */
from alembic import op
import sqlalchemy as sa


revision = "0007_system_wallet_accounts"
down_revision = "0006_scripe_sya_withdrawal_window"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.alter_column(
        "accounts",
        "wallet_code",
        existing_type=sa.String(length=3),
        type_=sa.String(length=4),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_accounts_wallet_code_length_by_system",
        "accounts",
        "wallet_code IS NULL OR "
        "(is_system = TRUE AND length(wallet_code) <= 4) OR "
        "(is_system = FALSE AND length(wallet_code) <= 3)",
    )


def downgrade() -> None:
    connection = op.get_bind()
    invalid_codes = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM accounts "
            "WHERE wallet_code IS NOT NULL AND length(wallet_code) > 3"
        )
    ).scalar_one()

    if invalid_codes:
        raise RuntimeError(
            "Cannot downgrade: four-character wallet codes exist."
        )

    op.drop_constraint(
        "ck_accounts_wallet_code_length_by_system",
        "accounts",
        type_="check",
    )
    op.alter_column(
        "accounts",
        "wallet_code",
        existing_type=sa.String(length=4),
        type_=sa.String(length=3),
        existing_nullable=True,
    )
    op.drop_column("accounts", "is_system")
