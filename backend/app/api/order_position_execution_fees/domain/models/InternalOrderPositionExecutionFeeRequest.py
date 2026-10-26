# /* ../NauTrader_Helm/payments-core/backend/app/api/order_position_execution_fees/domain/models/InternalOrderPositionExecutionFeeRequest.py */
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class InternalOrderPositionExecutionFeeRequest(BaseModel):
    user_id: UUID
    event_id: str = Field(min_length=1, max_length=256)
    mode: Literal["paper", "live", "mock", "backtests"]
    fee_type: Literal["order", "position_opening", "position_closing"]
    volume_usdt: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=18,
        decimal_places=6,
    )
    is_protective_order: bool = False
