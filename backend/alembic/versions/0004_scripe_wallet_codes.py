# /* payments-core/backend/alembic/versions/0004_scripe_wallet_codes.py */
from alembic import op
import sqlalchemy as sa


revision = "0004_scripe_wallet_codes"
down_revision = "0003_account_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("wallet_code", sa.String(length=2), nullable=True),
    )
    op.create_unique_constraint(
        "uq_accounts_owner_wallet_code",
        "accounts",
        ["owner_id", "wallet_code"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_accounts_owner_wallet_code",
        "accounts",
        type_="unique",
    )
    op.drop_column("accounts", "wallet_code")
