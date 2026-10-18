# /* ../NauTrader_Helm/payments-core/backend/alembic/versions/0006_scripe_sya_withdrawal_window.py */
from alembic import op
import sqlalchemy as sa


revision = "0006_scripe_sya_withdrawal_window"
down_revision = "0005_scripe_wallet_code_length"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scripe_sya_withdrawal_windows",
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("owner_id", "window_start"),
        sa.UniqueConstraint(
            "idempotency_key",
            name="uq_scripe_sya_withdrawal_idempotency_key",
        ),
    )


def downgrade() -> None:
    op.drop_table("scripe_sya_withdrawal_windows")
