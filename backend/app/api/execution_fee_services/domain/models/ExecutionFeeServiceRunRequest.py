# /* ../NauTrader_Helm/payments-core/backend/app/api/execution_fee_services/domain/models/ExecutionFeeServiceRunRequest.py */
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class ExecutionFeeServiceRunRequest(BaseModel):
    mode: Literal["paper", "live", "mock", "backtests"]
    volume_usdt: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=6)
    profit_usdt: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=6)
    conversion_rate: Decimal = Field(default=Decimal("1"), gt=0, max_digits=18, decimal_places=8)
