# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/scenarios/OrderPositionExecutionFeeScenarios.py */

from app.services.OrderPositionExecutionFee.domain.config.OrderPositionExecutionFeeConfig import (
    OrderPositionExecutionFeeConfig as Config,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeScenario import (
    ExecutionFeeScenario,
)
from app.services.OrderPositionExecutionFee.domain.strategies.RejectInsufficientFundsPolicy import (
    RejectInsufficientFundsPolicy,
)
from app.services.OrderPositionExecutionFee.domain.strategies.SkipInsufficientFundsPolicy import (
    SkipInsufficientFundsPolicy,
)


class OrderPositionExecutionFeeScenarios:
    @staticmethod
    def order() -> ExecutionFeeScenario:
        return ExecutionFeeScenario(
            tariff_key=Config.ORDER_TARIFF_KEY,
            destination_wallet_code=Config.ORDER_FEE_WALLET_CODE,
            idempotency_scope=Config.ORDER_IDEMPOTENCY_SCOPE,
            idempotency_prefix=Config.ORDER_IDEMPOTENCY_PREFIX,
            description_prefix=Config.ORDER_DESCRIPTION_PREFIX,
            insufficient_funds_policy=RejectInsufficientFundsPolicy(),
        )

    @staticmethod
    def position_opening() -> ExecutionFeeScenario:
        return ExecutionFeeScenario(
            tariff_key=Config.POSITION_TARIFF_KEY,
            destination_wallet_code=Config.POSITION_FEE_WALLET_CODE,
            idempotency_scope=Config.POSITION_IDEMPOTENCY_SCOPE,
            idempotency_prefix=f"{Config.POSITION_IDEMPOTENCY_PREFIX}:opening",
            description_prefix=Config.POSITION_DESCRIPTION_PREFIX,
            insufficient_funds_policy=RejectInsufficientFundsPolicy(),
        )

    @staticmethod
    def position_closing() -> ExecutionFeeScenario:
        return ExecutionFeeScenario(
            tariff_key=Config.POSITION_TARIFF_KEY,
            destination_wallet_code=Config.POSITION_FEE_WALLET_CODE,
            idempotency_scope=Config.POSITION_IDEMPOTENCY_SCOPE,
            idempotency_prefix=f"{Config.POSITION_IDEMPOTENCY_PREFIX}:closing",
            description_prefix="Position closing fee",
            insufficient_funds_policy=SkipInsufficientFundsPolicy(),
        )
