# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/domain/models/ParameterizedExecutionFeeResult.py */

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ParameterizedExecutionFeeResult:
    status: str
    amount_minor: int
    amount: Decimal
    band_key: str
    percent: str
