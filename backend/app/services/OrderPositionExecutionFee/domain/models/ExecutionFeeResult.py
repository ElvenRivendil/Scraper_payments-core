# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/models/ExecutionFeeResult.py */

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutionFeeResult:
    status: str
    amount_minor: int
    created: bool
    transaction: dict[str, Any] | None = None
