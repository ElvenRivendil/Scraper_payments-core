# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/models/ExecutionFeeTariff.py */
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionFeeTariff:
    mode: str
    tariff_type: str
    enabled: bool
    amount_minor: int
