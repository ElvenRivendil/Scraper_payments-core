# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/config/OneToManyConfig.py */
from app.services.SystemFundsConsolidation.domain.strategies.one_to_many.EqualDistributionStrategy import EqualDistributionStrategy
from app.services.SystemFundsConsolidation.domain.config.SystemFundsConsolidationConfig import (
    SystemFundsConsolidationConfig,
)


class OneToManyConfig(SystemFundsConsolidationConfig):
    EXECUTION_TYPE = "ONE_TO_MANY"
    SOURCE_WALLET_CODE = "SCAP"
    DESTINATION_WALLET_CODES: tuple[str, ...] = (
        "ITFP",
        "EWFP",
        "OCFP",
        "PCFP",
        "PTCP",
        "DPAP",
        "ILAP",
    )
    DISTRIBUTION_STRATEGY = EqualDistributionStrategy
    DESTINATION_WEIGHTS: dict[str, int] = {
        "ITFP": 1,
        "EWFP": 1,
        "OCFP": 1,
        "PCFP": 1,
        "PTCP": 1,
        "DPAP": 1,
        "ILAP": 1,
    }
    DESTINATION_PRIORITIES: dict[str, int] = {
        "ITFP": 0,
        "EWFP": 1,
        "OCFP": 2,
        "PCFP": 3,
        "PTCP": 4,
        "DPAP": 5,
        "ILAP": 6,
    }
    DESTINATION_MAX_AMOUNTS_MINOR: dict[str, int] = {}

