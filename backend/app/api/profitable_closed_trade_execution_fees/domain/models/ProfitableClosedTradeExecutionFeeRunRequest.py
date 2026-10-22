# /* ../NauTrader_Helm/payments-core/backend/app/api/profitable_closed_trade_execution_fees/domain/models/ProfitableClosedTradeExecutionFeeRunRequest.py */
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ProfitableClosedTradeExecutionFeeRunRequest(BaseModel):
    mode: Literal["paper", "live", "mock", "backtests"]
    profit_usdt: Decimal = Field(ge=0, max_digits=18, decimal_places=6)
