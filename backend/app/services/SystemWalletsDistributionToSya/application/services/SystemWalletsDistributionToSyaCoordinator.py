# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsDistributionToSya/application/services/SystemWalletsDistributionToSyaCoordinator.py */

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.services.SystemWalletsDistributionToSya.application.operations.SystemWalletsDistributionToSyaWriteOperation import (
    SystemWalletsDistributionToSyaWriteOperation,
)
from app.services.SystemWalletsDistributionToSya.application.services.SystemWalletsDistributionToSyaSnapshotReader import (
    SystemWalletsDistributionToSyaSnapshotReader,
)
from app.services.SystemWalletsDistributionToSya.domain.strategies.SystemWalletsDistributionToSyaAllocationCalculator import (
    SystemWalletsDistributionToSyaAllocationCalculator,
)

logger = logging.getLogger(__name__)


class SystemWalletsDistributionToSyaCoordinator:
    MAX_ATTEMPTS = 3

    @classmethod
    def execute(
        cls,
        session_factory: sessionmaker[Session],
        user_ids: list[UUID],
        *,
        execution_time: datetime,
    ) -> dict[str, Any]:
        if execution_time.tzinfo is None:
            raise ValueError("Execution time must be timezone-aware.")

        unique_user_ids = sorted(set(user_ids), key=str)
        last_error: Exception | None = None

        for attempt in range(1, cls.MAX_ATTEMPTS + 1):
            try:
                with session_factory() as snapshot_session:
                    snapshot = (
                        SystemWalletsDistributionToSyaSnapshotReader.read_snapshot(
                            snapshot_session,
                            unique_user_ids,
                        )
                    )

                user_balances = snapshot["user_er_balances_minor"]
                distribution_amount_minor = snapshot[
                    "system_balances_minor"
                ]["SPAP"][2]
                allocation = (
                    SystemWalletsDistributionToSyaAllocationCalculator.calculate(
                        user_balances,
                        distribution_amount_minor,
                    )
                )

                with session_factory() as write_session:
                    with write_session.begin():
                        result = (
                            SystemWalletsDistributionToSyaWriteOperation.execute(
                                write_session,
                                execution_time=execution_time,
                                user_ids=unique_user_ids,
                                user_er_balances_minor=user_balances,
                                er_total_minor=allocation["er_total_minor"],
                                distribution_amount_minor=distribution_amount_minor,
                            )
                        )

                result.update(
                    {
                        "status": "completed",
                        "attempt": attempt,
                        "users_total": len(unique_user_ids),
                        "users_with_positive_balance": allocation[
                            "users_with_positive_balance"
                        ],
                    }
                )
                logger.info(
                    "System wallets distribution to SYA completed: "
                    "attempt=%s users=%s er_total_minor=%s "
                    "distribution_minor=%s transfers=%s",
                    attempt,
                    len(unique_user_ids),
                    result["er_total_minor"],
                    result["distribution_amount_minor"],
                    result["transfer_count"],
                )
                return result
            except Exception as exc:
                last_error = exc
                logger.exception(
                    "System wallets distribution to SYA attempt failed: "
                    "attempt=%s/%s",
                    attempt,
                    cls.MAX_ATTEMPTS,
                )

        raise RuntimeError(
            "System wallets distribution to SYA failed after "
            f"{cls.MAX_ATTEMPTS} attempts: {last_error}"
        ) from last_error
