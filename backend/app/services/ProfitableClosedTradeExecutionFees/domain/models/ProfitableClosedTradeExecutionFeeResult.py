# /* ../NauTrader_Helm/payments-core/backend/app/services/ProfitableClosedTradeExecutionFees/domain/models/ProfitableClosedTradeExecutionFeeResult.py */
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ProfitableClosedTradeExecutionFeeResult:
    status: str
    amount_minor: int
    created: bool
    band_key: str
    percent: Decimal
    transaction: Any | None = None
