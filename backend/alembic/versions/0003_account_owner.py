"""Add owner UUID to accounts.

Revision ID: 0003_account_owner
Revises: 0002_reconcile_runs
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_account_owner"
down_revision = "0002_reconcile_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("owner_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_accounts_owner_id",
        "accounts",
        ["owner_id"],
        unique=False,
    )
    op.execute(sa.text("""
        UPDATE accounts
        SET owner_id = CAST(:demo_owner_id AS uuid)
        WHERE owner_id IS NULL
          AND name IN (
              'INR Mint Source', 'INR Treasury',
              'INR Alice Wallet', 'INR Corner Shop',
              'USD Mint Source', 'USD Treasury',
              'USD Alice Wallet', 'USD Corner Shop',
              'EUR Mint Source', 'EUR Treasury',
              'EUR Alice Wallet', 'EUR Corner Shop'
          )
    """).bindparams(
        demo_owner_id="00000000-0000-0000-0000-000000000000"
    ))


def downgrade() -> None:
    op.drop_index("ix_accounts_owner_id", table_name="accounts")
    op.drop_column("accounts", "owner_id")
