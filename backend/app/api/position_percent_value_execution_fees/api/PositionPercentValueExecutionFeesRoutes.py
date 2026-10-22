# /* ../NauTrader_Helm/payments-core/backend/app/api/position_percent_value_execution_fees/api/PositionPercentValueExecutionFeesRoutes.py */
from app.api.execution_fee_services.api.ExecutionFeeServiceRoutes import (
    ExecutionFeeServiceRoutes,
)
from app.api.position_percent_value_execution_fees.application.services.RunPositionPercentValueExecutionFeeManualService import (
    RunPositionPercentValueExecutionFeeManualService,
)
from app.services.PositionPercentValueExecutionFees.domain.config.PositionPercentValueExecutionFeesConfig import (
    PositionPercentValueExecutionFeesConfig,
)


class PositionPercentValueExecutionFeesRoutes(ExecutionFeeServiceRoutes):
    def __init__(self) -> None:
        super().__init__(
            service_name="position-percent-value-execution-fees",
            config=PositionPercentValueExecutionFeesConfig,
            executor=RunPositionPercentValueExecutionFeeManualService.execute,
        )
