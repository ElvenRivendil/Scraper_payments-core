# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/strategies/virtual_many_to_one/VirtualBalanceStrategy.py */
from abc import ABC, abstractmethod
from typing import Mapping


class VirtualBalanceStrategy(ABC):
    @abstractmethod
    def calculate(
        self,
        available_balances: Mapping[str, int],
        config: type,
    ) -> int:
        raise NotImplementedError
