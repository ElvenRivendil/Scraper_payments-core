# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/config/ManyToOneConfig.py */
from app.services.SystemFundsConsolidation.domain.config.SystemFundsConsolidationConfig import (
    SystemFundsConsolidationConfig,
)


class ManyToOneConfig(SystemFundsConsolidationConfig):
    EXECUTION_TYPE = "MANY_TO_ONE"
