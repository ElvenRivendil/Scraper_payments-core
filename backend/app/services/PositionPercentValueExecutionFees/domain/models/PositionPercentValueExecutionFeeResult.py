# /* ../NauTrader_Helm/payments-core/backend/app/services/PositionPercentValueExecutionFees/domain/models/PositionPercentValueExecutionFeeResult.py */

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PositionPercentValueExecutionFeeResult:
    status: str
    amount_minor: int
    created: bool
    band_key: str | None = None
    percent: str | None = None
    transaction: dict[str, Any] | None = None
