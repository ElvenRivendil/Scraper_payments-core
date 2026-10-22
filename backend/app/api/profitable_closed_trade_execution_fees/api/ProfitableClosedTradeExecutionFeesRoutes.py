# /* ../NauTrader_Helm/payments-core/backend/app/api/profitable_closed_trade_execution_fees/api/ProfitableClosedTradeExecutionFeesRoutes.py */
from app.api.execution_fee_services.api.ExecutionFeeServiceRoutes import (
    ExecutionFeeServiceRoutes,
)
from app.api.profitable_closed_trade_execution_fees.application.services.RunProfitableClosedTradeExecutionFeeManualService import (
    RunProfitableClosedTradeExecutionFeeManualService,
)
from app.services.ProfitableClosedTradeExecutionFees.domain.config.ProfitableClosedTradeExecutionFeesConfig import (
    ProfitableClosedTradeExecutionFeesConfig,
)


class ProfitableClosedTradeExecutionFeesRoutes(ExecutionFeeServiceRoutes):
    def __init__(self) -> None:
        super().__init__(
            service_name=ProfitableClosedTradeExecutionFeesConfig.SERVICE_NAME,
            config=ProfitableClosedTradeExecutionFeesConfig,
            executor=RunProfitableClosedTradeExecutionFeeManualService.execute,
            input_field="profit_usdt",
        )
