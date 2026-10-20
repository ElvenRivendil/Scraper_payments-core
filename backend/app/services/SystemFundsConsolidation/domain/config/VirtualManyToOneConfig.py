# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/config/VirtualManyToOneConfig.py */
from app.services.SystemFundsConsolidation.domain.strategies.virtual_many_to_one.SumAvailableBalancesStrategy import SumAvailableBalancesStrategy
from app.services.SystemFundsConsolidation.domain.config.SystemFundsConsolidationConfig import (
    SystemFundsConsolidationConfig,
)


class VirtualManyToOneConfig(SystemFundsConsolidationConfig):
    EXECUTION_TYPE = "VIRTUAL_MANY_TO_ONE"
    BALANCE_STRATEGY = SumAvailableBalancesStrategy
    SOURCE_WALLET_WEIGHTS: dict[str, int] = {
        "ITFP": 1,
        "EWFP": 1,
        "OCFP": 1,
        "PCFP": 1,
        "PTCP": 1,
        "DPAP": 1,
        "ILAP": 1,
    }

