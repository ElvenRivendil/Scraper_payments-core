# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/domain/models/ParameterizedExecutionFeeResult.py */

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterizedExecutionFeeResult:
    status: str
    amount_minor: int
    band_key: str
    percent: str
