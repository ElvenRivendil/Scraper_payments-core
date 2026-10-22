# /* ../NauTrader_Helm/payments-core/backend/app/services/PositionPercentValueExecutionFees/domain/config/PositionPercentValueExecutionFeesConfig.py */

from app.services.ParameterizedExecutionFee.domain.config.ParameterizedExecutionFeeConfig import (
    ParameterizedExecutionFeeConfig,
)


class PositionPercentValueExecutionFeesConfig(ParameterizedExecutionFeeConfig):
    TARIFF_ENTITY_KEY = "profit_trade_commission"
    TARIFF_KEY = "profit_percent"
    TARIFF_RESOLVER_STRATEGY = "banded_percentage"

    WALLET_OWNER_STRATEGY = "user_id"
    SOURCE_WALLET_CODE = "IS"
    TARGET_WALLET_CODE = "ITF"

    IDEMPOTENCY_SCOPE = "position_percent_value_execution_fee"
    IDEMPOTENCY_PREFIX = "position-percent-value-execution-fee"
    DESCRIPTION_PREFIX = "Position percent value execution fee"

    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "position_percent_value_execution_fees.log"
