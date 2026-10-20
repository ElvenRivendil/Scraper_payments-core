# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/strategies/virtual_many_to_one/WeightedAvailableBalancesStrategy.py */
from typing import Mapping

from app.services.SystemFundsConsolidation.domain.strategies.virtual_many_to_one.VirtualBalanceStrategy import (
    VirtualBalanceStrategy,
)


class WeightedAvailableBalancesStrategy(VirtualBalanceStrategy):
    def calculate(
        self,
        available_balances: Mapping[str, int],
        config: type,
    ) -> int:
        weights = config.SOURCE_WALLET_WEIGHTS
        if set(weights) != set(available_balances):
            raise ValueError("Source wallet weights must match available balance keys.")
        if any(weight < 0 for weight in weights.values()):
            raise ValueError("Source wallet weights must not be negative.")

        total_weight = sum(weights.values())
        if total_weight <= 0:
            raise ValueError("At least one source wallet weight must be positive.")

        numerator = sum(
            available_balances[wallet_code] * weights[wallet_code]
            for wallet_code in available_balances
        )
        return numerator // total_weight
