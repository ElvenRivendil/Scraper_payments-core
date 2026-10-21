# /* ../NauTrader_Helm/payments-core/backend/app/workers/tasks.py */
from __future__ import annotations

import logging
from pathlib import Path
from sqlalchemy import text
from datetime import UTC, datetime

from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient
from app.core.config import get_settings
from app.core.db import create_engine_and_session
from app.core.execution_logging.ServiceExecutionLogger import ServiceExecutionLogger
from app.api.system_wallets_management.application.services.SystemFundsDistributionSharesState import (
    SystemFundsDistributionSharesState,
)
from app.services.UserFundsCollection.domain.config.UserFundsCollectionConfig import UserFundsCollectionConfig
from app.services.SystemFundsConsolidation.domain.config.SystemFundsConsolidationConfig import SystemFundsConsolidationConfig
from app.services.SystemFundsConsolidation.domain.config.SystemFundsDistributionConfig import SystemFundsDistributionConfig
from app.services.SystemWalletsAggregation.domain.config.SystemWalletsAggregationConfig import (
    SystemWalletsAggregationConfig,
)
from app.services.SystemWalletsAggregation.application.services.SystemWalletsAggregationCoordinator import (
    SystemWalletsAggregationCoordinator,
)
from app.services.SystemWalletsDistributionToSya.domain.config.SystemWalletsDistributionToSyaConfig import (
    SystemWalletsDistributionToSyaConfig,
)
from app.services.SystemWalletsDistributionToSya.application.services.SystemWalletsDistributionToSyaCoordinator import (
    SystemWalletsDistributionToSyaCoordinator,
)
from app.services.UserFundsCollection.application.services.UserFundsCollectionService import (
    UserFundsCollectionService,
)
from app.services.SystemFundsConsolidation.application.operations.ManyToOneOperation import (
    ManyToOneOperation,
)
from app.services.SystemFundsConsolidation.application.operations.OneToManyOperation import (
    OneToManyOperation,
)
from app.services.webhooks import process_webhook_event
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()
_engine, _session_factory = create_engine_and_session(settings.database_url)


@celery_app.task(name="payments_core.noop")
def noop() -> str:
    return "ok"


@celery_app.task(name="payments_core.process_webhook")
def process_webhook(event_id: str) -> dict:
    def enqueue_retry(next_event_id: str, countdown: int) -> None:
        try:
            process_webhook.apply_async(args=[next_event_id], countdown=countdown)
        except Exception:
            process_webhook.apply(args=[next_event_id])

    with _session_factory() as session:
        return process_webhook_event(
            session,
            event_id=event_id,
            enqueue_retry=enqueue_retry,
        )


@celery_app.task(name="payments_core.user_funds_collection_schedule_probe")
def user_funds_collection_schedule_probe() -> dict[str, int | str]:
    execution = ServiceExecutionLogger(
        service_name="user_funds_collection",
        log_file=Path(UserFundsCollectionConfig.LOG_DIRECTORY) / UserFundsCollectionConfig.LOG_FILENAME,
        console_logger=logger,
    )
    with execution:
        collection_hour = datetime.now(UTC).replace(
            minute=0,
            second=0,
            microsecond=0,
        )
        if not settings.helm_internal_api_secret:
            message = "Helm internal secret is not configured"
            execution.record_error(message)
            logger.error("User funds collection aborted: %s", message)
            execution.set_status("configuration_error")
            return {
                "status": "configuration_error",
                "users_total": 0,
                "users_succeeded": 0,
                "users_failed": 0,
            }

        helm_client = HelmApiClient(settings.helm_auth_base_url)
        try:
            user_ids = helm_client.get_active_user_ids(
                settings.helm_internal_api_secret,
            )
        except Exception as exc:
            execution.record_error(
                "Active users could not be loaded",
                exception=exc,
            )
            logger.exception("User funds collection aborted: active users could not be loaded")
            execution.set_status("discovery_error")
            return {
                "status": "discovery_error",
                "users_total": 0,
                "users_succeeded": 0,
                "users_failed": 0,
            }

        succeeded = 0
        failed = 0
        for user_id in user_ids:
            try:
                with _session_factory() as session:
                    UserFundsCollectionService.collect_for_user(
                        session,
                        user_id,
                        collection_hour=collection_hour,
                    )
                succeeded += 1
            except Exception as exc:
                failed += 1
                execution.record_error(
                    f"User funds collection failed for user_id={user_id}",
                    exception=exc,
                )
                logger.exception(
                    "User funds collection failed for user_id=%s hour=%s",
                    user_id,
                    collection_hour.strftime("%Y%m%dT%H"),
                )

        status = "completed" if failed == 0 else "completed_with_errors"
        execution.set_status(status)
        logger.info(
            "Scheduled user funds collection finished: hour=%s total=%s "
            "succeeded=%s failed=%s",
            collection_hour.strftime("%Y%m%dT%H"),
            len(user_ids),
            succeeded,
            failed,
        )
        return {
            "status": status,
            "users_total": len(user_ids),
            "users_succeeded": succeeded,
            "users_failed": failed,
        }


@celery_app.task(name="payments_core.system_funds_distribution_hourly")
def system_funds_distribution_hourly() -> dict[str, int | str]:
    execution = ServiceExecutionLogger(
        service_name="system_funds_distribution",
        log_file=Path(SystemFundsDistributionConfig.LOG_DIRECTORY) / SystemFundsDistributionConfig.LOG_FILENAME,
        console_logger=logger,
    )
    with execution:
        execution_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
        try:
            shares = SystemFundsDistributionSharesState().get_shares()
            runtime_config = type(
                "RuntimeSystemFundsDistributionConfig",
                (SystemFundsDistributionConfig,),
                {"DESTINATION_WEIGHTS": shares},
            )
            with _session_factory() as session:
                transferred = OneToManyOperation.execute(
                    session,
                    execution_time=execution_time,
                    config_class=runtime_config,
                )
        except Exception as exc:
            execution.record_error("System funds distribution failed", exception=exc)
            execution.set_status("failed")
            logger.exception(
                "System funds distribution failed: hour=%s",
                execution_time.strftime("%Y%m%dT%H"),
            )
            raise

        amount_minor = sum(transferred.values())
        execution.set_status("completed")
        logger.info(
            "System funds distribution finished: hour=%s wallets_transferred=%s amount_minor=%s",
            execution_time.strftime("%Y%m%dT%H"),
            len(transferred),
            amount_minor,
        )
        return {
            "status": "completed",
            "wallets_transferred": len(transferred),
            "amount_minor": amount_minor,
        }


@celery_app.task(name="payments_core.system_funds_consolidation_hourly")
def system_funds_consolidation_hourly() -> dict[str, int | str]:
    execution = ServiceExecutionLogger(
        service_name="system_funds_consolidation",
        log_file=Path(SystemFundsConsolidationConfig.LOG_DIRECTORY) / SystemFundsConsolidationConfig.LOG_FILENAME,
        console_logger=logger,
    )
    with execution:
        execution_time = datetime.now(UTC).replace(
            minute=0,
            second=0,
            microsecond=0,
        )
        try:
            with _session_factory() as session:
                transferred = ManyToOneOperation.execute(
                    session,
                    execution_time=execution_time,
                )
        except Exception as exc:
            execution.record_error(
                "System funds consolidation failed",
                exception=exc,
            )
            execution.set_status("failed")
            logger.exception(
                "System funds consolidation failed: hour=%s",
                execution_time.strftime("%Y%m%dT%H"),
            )
            raise

        amount_minor = sum(transferred.values())
        execution.set_status("completed")
        logger.info(
            "System funds consolidation finished: hour=%s "
            "wallets_transferred=%s amount_minor=%s",
            execution_time.strftime("%Y%m%dT%H"),
            len(transferred),
            amount_minor,
        )
        return {
            "status": "completed",
            "wallets_transferred": len(transferred),
            "amount_minor": amount_minor,
        }


@celery_app.task(name="payments_core.system_wallets_distribution_to_sya_hourly")
def system_wallets_distribution_to_sya_hourly() -> dict:
    execution = ServiceExecutionLogger(
        service_name="system_wallets_distribution_to_sya",
        log_file=Path("logs") / "system_wallets_distribution_to_sya.log",
        console_logger=logger,
    )
    with execution:
        lock_connection = _engine.connect()
        lock_acquired = False
        try:
            lock_acquired = bool(
                lock_connection.execute(
                    text("SELECT pg_try_advisory_lock(:lock_key)"),
                    {"lock_key": 7483921046218},
                ).scalar_one()
            )
            if not lock_acquired:
                execution.set_status("skipped")
                return {"status": "skipped", "users_total": 0, "transfer_count": 0}

            execution_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
            if not settings.helm_internal_api_secret:
                message = "Helm internal secret is not configured"
                execution.record_error(message)
                execution.set_status("configuration_error")
                return {"status": "configuration_error", "users_total": 0, "transfer_count": 0}

            try:
                helm_client = HelmApiClient(settings.helm_auth_base_url)
                user_ids = helm_client.get_active_user_ids(settings.helm_internal_api_secret)
            except Exception as exc:
                execution.record_error("Active users could not be loaded", exception=exc)
                execution.set_status("discovery_error")
                logger.exception("System wallets distribution to SYA: active user discovery failed")
                return {"status": "discovery_error", "users_total": 0, "transfer_count": 0}

            result = SystemWalletsDistributionToSyaCoordinator.execute(
                _session_factory,
                user_ids,
                execution_time=execution_time,
            )
            execution.set_status(result["status"])
            logger.info(
                "System wallets distribution to SYA finished: users=%s transfers=%s amount_minor=%s",
                result.get("users_total", len(user_ids)),
                result.get("transfer_count", 0),
                result.get("transferred_minor", 0),
            )
            return result
        except Exception as exc:
            execution.record_error("System wallets distribution to SYA failed", exception=exc)
            execution.set_status("failed")
            raise
        finally:
            try:
                if lock_acquired:
                    lock_connection.execute(
                        text("SELECT pg_advisory_unlock(:lock_key)"),
                        {"lock_key": 7483921046218},
                    )
            except Exception:
                logger.exception("Failed to release system wallets distribution to SYA advisory lock")
                _engine.dispose()
                raise
            finally:
                lock_connection.close()


@celery_app.task(name="payments_core.system_wallets_aggregation_hourly")
def system_wallets_aggregation_hourly() -> dict:
    execution = ServiceExecutionLogger(
        service_name="system_wallets_aggregation",
        log_file=Path(SystemWalletsAggregationConfig.LOG_DIRECTORY)
        / SystemWalletsAggregationConfig.LOG_FILENAME,
        console_logger=logger,
    )
    with execution:
        lock_connection = _engine.connect()
        lock_acquired = False
        try:
            lock_acquired = bool(
                lock_connection.execute(
                    text("SELECT pg_try_advisory_lock(:lock_key)"),
                    {"lock_key": 7483921046217},
                ).scalar_one()
            )
            if not lock_acquired:
                execution.set_status("skipped")
                logger.info(
                    "System wallets aggregation skipped: another run is active"
                )
                return {
                    "status": "skipped",
                    "pairs_total": 0,
                    "pairs_succeeded": 0,
                    "pairs_failed": 0,
                    "users_total": 0,
                    "target_balance_minor": 0,
                    "amount_minor": 0,
                    "results": [],
                }
            execution_time = datetime.now(UTC).replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            if not settings.helm_internal_api_secret:
                message = "Helm internal secret is not configured"
                execution.record_error(message)
                execution.set_status("configuration_error")
                logger.error("System wallets aggregation aborted: %s", message)
                return {
                    "status": "configuration_error",
                    "pairs_total": 0,
                    "pairs_succeeded": 0,
                    "pairs_failed": 0,
                    "users_total": 0,
                    "target_balance_minor": 0,
                    "amount_minor": 0,
                    "results": [],
                }

            try:
                helm_client = HelmApiClient(settings.helm_auth_base_url)
                user_ids = helm_client.get_active_user_ids(
                    settings.helm_internal_api_secret,
                )
            except Exception as exc:
                execution.record_error(
                    "Active users could not be loaded",
                    exception=exc,
                )
                execution.set_status("discovery_error")
                logger.exception(
                    "System wallets aggregation aborted: active users could not be loaded"
                )
                return {
                    "status": "discovery_error",
                    "pairs_total": 0,
                    "pairs_succeeded": 0,
                    "pairs_failed": 0,
                    "users_total": 0,
                    "target_balance_minor": 0,
                    "amount_minor": 0,
                    "results": [],
                }

            result = SystemWalletsAggregationCoordinator.execute(
                _session_factory,
                user_ids,
                execution_time=execution_time,
            )
            for pair in result["results"]:
                if pair["status"] != "completed":
                    execution.record_error(
                        "Wallet pair failed: "
                        f"{pair['source_wallet_code']} -> "
                        f"{pair['destination_wallet_code']}: "
                        f"{pair.get('error', 'Unknown error')}"
                    )

            execution.set_status(result["status"])
            logger.info(
                "System wallets aggregation finished: hour=%s users=%s "
                "pairs_succeeded=%s pairs_failed=%s target_balance_minor=%s "
                "amount_minor=%s",
                execution_time.strftime("%Y%m%dT%H"),
                len(user_ids),
                result["pairs_succeeded"],
                result["pairs_failed"],
                result["target_balance_minor"],
                result["amount_minor"],
            )
            return result
        finally:
            try:
                if lock_acquired:
                    lock_connection.execute(
                        text("SELECT pg_advisory_unlock(:lock_key)"),
                        {"lock_key": 7483921046217},
                    )
            except Exception:
                logger.exception(
                    "Failed to release system wallets aggregation advisory lock"
                )
                _engine.dispose()
                raise
            finally:
                lock_connection.close()
