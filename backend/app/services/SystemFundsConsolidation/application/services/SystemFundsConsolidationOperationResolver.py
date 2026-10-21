# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/application/services/SystemFundsConsolidationOperationResolver.py */
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.SystemFundsConsolidation.application.operations.ManyToOneOperation import (
    ManyToOneOperation,
)
from app.services.SystemFundsConsolidation.application.operations.OneToManyOperation import (
    OneToManyOperation,
)
from app.services.SystemFundsConsolidation.application.operations.VirtualManyToOneOperation import (
    VirtualManyToOneOperation,
)
from app.services.SystemFundsConsolidation.domain.value_objects.SystemFundsConsolidationMode import (
    SystemFundsConsolidationMode,
)


class SystemFundsConsolidationOperationResolver:
    OPERATIONS = {
        SystemFundsConsolidationMode.MANY_TO_ONE: ManyToOneOperation,
        SystemFundsConsolidationMode.ONE_TO_MANY: OneToManyOperation,
        SystemFundsConsolidationMode.VIRTUAL_MANY_TO_ONE: VirtualManyToOneOperation,
    }

    @classmethod
    def resolve(
        cls,
        mode: str | SystemFundsConsolidationMode,
    ) -> Any:
        selected_mode = SystemFundsConsolidationMode.parse(mode)
        return cls.OPERATIONS[selected_mode]

    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        execution_time: datetime,
        mode: str | SystemFundsConsolidationMode,
    ) -> dict[str, int]:
        operation = cls.resolve(mode)
        return operation.execute(
            session,
            execution_time=execution_time,
        )
