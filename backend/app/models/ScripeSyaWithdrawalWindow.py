# /* ../NauTrader_Helm/payments-core/backend/app/models/ScripeSyaWithdrawalWindow.py */
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.db import Base


class ScripeSyaWithdrawalWindow(Base):
    __tablename__ = "scripe_sya_withdrawal_windows"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_scripe_sya_withdrawal_idempotency_key",
        ),
    )

    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    response_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
