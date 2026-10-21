# /* ../NauTrader_Helm/payments-core/backend/app/api/order_position_execution_fees/domain/models/OrderPositionExecutionFeesRunRequest.py */
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class OrderPositionExecutionFeesRunRequest(BaseModel):
    mode: Literal["paper", "live", "mock", "backtests"]
    volume_usdt: Decimal = Field(ge=0, max_digits=18, decimal_places=6)
