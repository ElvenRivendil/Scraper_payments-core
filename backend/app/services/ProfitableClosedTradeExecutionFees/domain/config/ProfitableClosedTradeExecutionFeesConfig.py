# /* ../NauTrader_Helm/payments-core/backend/app/services/ProfitableClosedTradeExecutionFees/domain/config/ProfitableClosedTradeExecutionFeesConfig.py */
from app.services.ParameterizedExecutionFee.domain.config.ParameterizedExecutionFeeConfig import (
    ParameterizedExecutionFeeConfig,
)


class ProfitableClosedTradeExecutionFeesConfig(ParameterizedExecutionFeeConfig):
    SERVICE_NAME = "profitable_closed_trade_execution_fees"
    PROFIT_CURRENCY_CODE = "USDT"
    CURRENCY_CODE = "SCR"
    TARIFF_ENTITY_KEY = "position_collateral"
    TARIFF_KEY = "collateral_percent"
    TARIFF_RESOLVER_STRATEGY = "banded_percentage"
    WALLET_OWNER_STRATEGY = "user_id"
    SOURCE_WALLET_CODE = "IS"
    TARGET_WALLET_CODE = "ER"
    IDEMPOTENCY_SCOPE = "profitable_closed_trade_execution_fee"
    IDEMPOTENCY_PREFIX = "profitable-closed-trade-execution-fee"
    DESCRIPTION_PREFIX = "Profitable closed trade execution fee"
    LOG_DIRECTORY = "logs"
    LOG_FILENAME = "profitable_closed_trade_execution_fees.log"
    INPUT_FIELD = "profit_usdt"
