# /* payments-core/backend/alembic/versions/0005_scripe_wallet_code_length.py */
from alembic import op
import sqlalchemy as sa


revision = "0005_scripe_wallet_code_length"
down_revision = "0004_scripe_wallet_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "accounts",
        "wallet_code",
        existing_type=sa.String(length=2),
        type_=sa.String(length=3),
        existing_nullable=True,
    )


def downgrade() -> None:
    connection = op.get_bind()
    long_codes = connection.execute(
        sa.text(
            "SELECT COUNT(*) FROM accounts "
            "WHERE wallet_code IS NOT NULL AND length(wallet_code) > 2"
        )
    ).scalar_one()

    if long_codes:
        raise RuntimeError(
            "Cannot downgrade wallet_code to length 2 while three-character "
            "wallet codes exist."
        )

    op.alter_column(
        "accounts",
        "wallet_code",
        existing_type=sa.String(length=3),
        type_=sa.String(length=2),
        existing_nullable=True,
    )
