# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsAggregation/application/services/SystemWalletsAggregationCoordinator.py */

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.services.SystemWalletsAggregation.application.operations.SystemWalletsAggregationVirtualManyToOneOperation import (
    SystemWalletsAggregationVirtualManyToOneOperation,
)
from app.services.SystemWalletsAggregation.application.services.SystemWalletsAggregationUserWalletReader import (
    SystemWalletsAggregationUserWalletReader,
)
from app.services.SystemWalletsAggregation.domain.config.SystemWalletsAggregationConfig import (
    SystemWalletsAggregationConfig,
)
from app.services.SystemWalletsAggregation.domain.strategies.SystemWalletsAggregationBalanceCalculator import (
    SystemWalletsAggregationBalanceCalculator,
)

logger = logging.getLogger(__name__)


class SystemWalletsAggregationCoordinator:
    @classmethod
    def execute(
        cls,
        session_factory: sessionmaker[Session],
        user_ids: list[UUID],
        *,
        execution_time: datetime,
    ) -> dict[str, Any]:
        SystemWalletsAggregationConfig.validate()
        results: list[dict[str, Any]] = []
        succeeded = 0
        failed = 0
        total_target_minor = 0
        total_adjustment_minor = 0

        for source_wallet_code, destination_wallet_code in (
            SystemWalletsAggregationConfig.get_wallet_pairs()
        ):
            pair_result: dict[str, Any] = {
                "source_wallet_code": source_wallet_code,
                "destination_wallet_code": destination_wallet_code,
                "status": "failed",
                "users_total": len(user_ids),
                "users_with_wallet": 0,
                "target_balance_minor": 0,
                "delta_minor": 0,
                "amount_minor": 0,
                "created": 0,
            }

            try:
                with session_factory() as session:
                    snapshot = (
                        SystemWalletsAggregationUserWalletReader.read_snapshot(
                            session,
                            user_ids,
                            wallet_code=source_wallet_code,
                        )
                    )

                target_balance_minor = (
                    SystemWalletsAggregationBalanceCalculator.calculate(
                        snapshot
                    )
                )
                pair_result["users_with_wallet"] = len(snapshot)
                pair_result["target_balance_minor"] = target_balance_minor

                with session_factory() as session:
                    write_result = (
                        SystemWalletsAggregationVirtualManyToOneOperation.execute(
                            session,
                            execution_time=execution_time,
                            source_wallet_code=source_wallet_code,
                            destination_wallet_code=destination_wallet_code,
                            target_balance_minor=target_balance_minor,
                        )
                    )

                pair_result.update(write_result)
                pair_result["status"] = "completed"
                succeeded += 1
                total_target_minor += target_balance_minor
                total_adjustment_minor += write_result["amount_minor"]
                logger.info(
                    "System wallets aggregation pair completed: "
                    "source=%s destination=%s users=%s target_minor=%s "
                    "delta_minor=%s created=%s",
                    source_wallet_code,
                    destination_wallet_code,
                    len(snapshot),
                    target_balance_minor,
                    write_result["delta_minor"],
                    write_result["created"],
                )
            except Exception as exc:
                failed += 1
                pair_result["error"] = str(exc)
                logger.exception(
                    "System wallets aggregation pair failed: source=%s destination=%s",
                    source_wallet_code,
                    destination_wallet_code,
                )

            results.append(pair_result)

        status = (
            "completed"
            if failed == 0
            else "completed_with_errors"
            if succeeded > 0
            else "failed"
        )

        return {
            "status": status,
            "pairs_total": len(results),
            "pairs_succeeded": succeeded,
            "pairs_failed": failed,
            "users_total": len(user_ids),
            "target_balance_minor": total_target_minor,
            "amount_minor": total_adjustment_minor,
            "results": results,
        }
