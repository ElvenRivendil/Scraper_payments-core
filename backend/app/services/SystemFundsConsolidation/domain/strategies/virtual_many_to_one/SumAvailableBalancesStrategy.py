# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/strategies/virtual_many_to_one/SumAvailableBalancesStrategy.py */
from typing import Mapping

from app.services.SystemFundsConsolidation.domain.strategies.virtual_many_to_one.VirtualBalanceStrategy import (
    VirtualBalanceStrategy,
)


class SumAvailableBalancesStrategy(VirtualBalanceStrategy):
    def calculate(
        self,
        available_balances: Mapping[str, int],
        config: type,
    ) -> int:
        if any(balance < 0 for balance in available_balances.values()):
            raise ValueError("Available balances must not be negative.")
        return sum(available_balances.values())
