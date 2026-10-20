# /* ../NauTrader_Helm/payments-core/backend/alembic/versions/0009_virtual_consolidation.py */
from alembic import op


revision = "0009_virtual_consolidation"
down_revision = "0008_demo_account_marker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE transaction_type "
        "ADD VALUE IF NOT EXISTS 'VIRTUAL_CONSOLIDATION'"
    )


def downgrade() -> None:
    raise RuntimeError(
        "Downgrade is intentionally unsupported: PostgreSQL enum values "
        "cannot be safely removed while transactions may reference them."
    )
