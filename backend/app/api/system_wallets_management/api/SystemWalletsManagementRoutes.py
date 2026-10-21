# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/api/SystemWalletsManagementRoutes.py */
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.system_wallets_management.application.services.SystemWalletsManagementConfigService import (
    SystemWalletsManagementConfigService,
)
from app.api.system_wallets_management.domain.models.SystemWalletsManagementConfigResponse import (
    SystemWalletsManagementConfigResponse,
)
from app.api.system_wallets_management.application.services.SystemWalletsManagementTaskService import (
    SystemWalletsManagementTaskService,
)
from app.api.system_wallets_management.domain.models.SystemWalletsManagementTaskUpdateRequest import (
    SystemWalletsManagementTaskUpdateRequest,
)
from app.api.system_wallets_management.domain.models.SystemFundsDistributionSharesUpdateRequest import (
    SystemFundsDistributionSharesUpdateRequest,
)
from app.api.system_wallets_management.application.services.SystemFundsDistributionSharesState import (
    SystemFundsDistributionSharesState,
)
from app.api.system_wallets_management.domain.models.SystemWalletsManagementTaskActionResponse import (
    SystemWalletsManagementTaskActionResponse,
)
from app.api.system_wallets_management.domain.models.SystemWalletsManagementTaskStateResponse import (
    SystemWalletsManagementTaskStateResponse,
)
from pathlib import Path

from app.core.auth import AuthenticatedUser, require_current_user
from app.services.UserFundsCollection.domain.config.UserFundsCollectionConfig import UserFundsCollectionConfig
from app.services.SystemFundsConsolidation.domain.config.SystemFundsConsolidationConfig import SystemFundsConsolidationConfig
from app.services.SystemFundsConsolidation.domain.config.SystemFundsDistributionConfig import SystemFundsDistributionConfig
from app.core.authorization.SystemWalletAccessPolicy import SystemWalletAccessPolicy


class SystemWalletsManagementRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/admin/system-wallets-management",
            tags=["admin-system-wallets-management"],
        )
        self.policy = SystemWalletAccessPolicy()
        self.service = SystemWalletsManagementConfigService()
        self.task_service = SystemWalletsManagementTaskService()
        self.distribution_shares_state = SystemFundsDistributionSharesState()
        self.router.add_api_route(
            "/tasks/{task_id}",
            self.get_task_state,
            methods=["GET"],
            response_model=SystemWalletsManagementTaskStateResponse,
        )
        self.router.add_api_route(
            "/tasks/{task_id}",
            self.update_task,
            methods=["PATCH"],
            response_model=SystemWalletsManagementTaskActionResponse,
        )
        self.router.add_api_route(
            "/tasks/{task_id}/logs",
            self.get_task_log,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/tasks/{task_id}/logs",
            self.clear_task_log,
            methods=["DELETE"],
        )
        self.router.add_api_route(
            "/tasks/{task_id}/run",
            self.run_task,
            methods=["POST"],
            response_model=SystemWalletsManagementTaskActionResponse,
        )
        self.router.add_api_route(
            "/config",
            self.get_config,
            methods=["GET"],
            response_model=SystemWalletsManagementConfigResponse,
        )
        self.router.add_api_route(
            "/distribution-shares",
            self.get_distribution_shares,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/distribution-shares",
            self.update_distribution_shares,
            methods=["PATCH"],
        )

    def get_task_log(
        self,
        task_id: str,
        request: Request,
        limit_bytes: int = Query(default=12000, ge=1, le=50000),
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, str | int | bool]:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)

        if task_id == self.service.USER_FUNDS_TASK_ID:
            log_directory = UserFundsCollectionConfig.LOG_DIRECTORY
            log_filename = UserFundsCollectionConfig.LOG_FILENAME
        elif task_id == self.service.SYSTEM_FUNDS_TASK_ID:
            log_directory = SystemFundsConsolidationConfig.LOG_DIRECTORY
            log_filename = SystemFundsConsolidationConfig.LOG_FILENAME
        elif task_id == self.service.SYSTEM_FUNDS_DISTRIBUTION_TASK_ID:
            log_directory = SystemFundsDistributionConfig.LOG_DIRECTORY
            log_filename = SystemFundsDistributionConfig.LOG_FILENAME
        else:
            raise HTTPException(status_code=404, detail="Unknown task")

        log_path = Path(__file__).resolve().parents[4] / log_directory / log_filename
        try:
            with log_path.open("rb") as log_file:
                log_file.seek(0, 2)
                total_bytes = log_file.tell()
                start = max(0, total_bytes - limit_bytes)
                log_file.seek(start)
                content = log_file.read(limit_bytes)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Task log is not available yet") from None
        except OSError:
            raise HTTPException(status_code=503, detail="Unable to read task log") from None

        if start > 0:
            newline_index = content.find(b"\\n")
            if newline_index >= 0:
                content = content[newline_index + 1:]

        return {
            "task_id": task_id,
            "content": content.decode("utf-8", errors="replace"),
            "limit_bytes": limit_bytes,
            "truncated": start > 0,
        }

    def clear_task_log(
        self,
        task_id: str,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, str | bool]:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)

        if task_id == self.service.USER_FUNDS_TASK_ID:
            log_directory = UserFundsCollectionConfig.LOG_DIRECTORY
            log_filename = UserFundsCollectionConfig.LOG_FILENAME
        elif task_id == self.service.SYSTEM_FUNDS_TASK_ID:
            log_directory = SystemFundsConsolidationConfig.LOG_DIRECTORY
            log_filename = SystemFundsConsolidationConfig.LOG_FILENAME
        elif task_id == self.service.SYSTEM_FUNDS_DISTRIBUTION_TASK_ID:
            log_directory = SystemFundsDistributionConfig.LOG_DIRECTORY
            log_filename = SystemFundsDistributionConfig.LOG_FILENAME
        else:
            raise HTTPException(status_code=404, detail="Unknown task")

        log_path = Path(__file__).resolve().parents[4] / log_directory / log_filename
        try:
            with log_path.open("wb"):
                pass
        except OSError:
            raise HTTPException(status_code=503, detail="Unable to clear task log") from None

        return {"task_id": task_id, "cleared": True}

    def get_config(
        self,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> SystemWalletsManagementConfigResponse:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)
        return self.service.get_config()

    def get_distribution_shares(
        self,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, list[dict[str, str | int]]]:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)
        try:
            shares = self.distribution_shares_state.get_shares()
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Unable to read distribution shares",
            ) from None
        return {
            "destination_shares": [
                {"wallet_code": code, "percentage": shares[code]}
                for code in ("SPAP", "WRAP")
            ]
        }

    def update_distribution_shares(
        self,
        payload: SystemFundsDistributionSharesUpdateRequest,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> dict[str, list[dict[str, str | int]]]:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)
        try:
            shares = self.distribution_shares_state.update_shares(
                payload.spap_percentage,
                payload.wrap_percentage,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Unable to save distribution shares",
            ) from None
        return {
            "destination_shares": [
                {"wallet_code": code, "percentage": shares[code]}
                for code in ("SPAP", "WRAP")
            ]
        }

    def get_task_state(
        self,
        task_id: str,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> SystemWalletsManagementTaskStateResponse:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)
        try:
            return SystemWalletsManagementTaskStateResponse(
                **self.task_service.get_state(task_id)
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Unknown task") from None
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Unable to read task state",
            ) from None

    def update_task(
        self,
        task_id: str,
        payload: SystemWalletsManagementTaskUpdateRequest,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> SystemWalletsManagementTaskActionResponse:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)
        try:
            state = self.task_service.update_state(
                task_id,
                enabled=payload.enabled,
                schedule_minute_utc=payload.schedule_minute_utc,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Unknown task") from None
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Unable to update task state",
            ) from None
        return SystemWalletsManagementTaskActionResponse(
            task_id=task_id,
            status="updated",
            enabled=state["enabled"],
            schedule_minute_utc=state["schedule_minute_utc"],
            message="Task schedule settings updated",
            celery_task_id=None,
        )

    def run_task(
        self,
        task_id: str,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> SystemWalletsManagementTaskActionResponse:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)
        try:
            result = self.task_service.queue_task(task_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Unknown task") from None
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Unable to queue task",
            ) from None
        return SystemWalletsManagementTaskActionResponse(
            task_id=task_id,
            status="queued",
            enabled=result["enabled"],
            schedule_minute_utc=result["schedule_minute_utc"],
            message=result["message"],
            celery_task_id=result["celery_task_id"],
        )

    @staticmethod
    def _require_real_user(
        request: Request,
        current_user: AuthenticatedUser,
    ) -> None:
        if current_user.id.int == 0 or getattr(request.state, "public_demo", False):
            raise HTTPException(
                status_code=401,
                detail="Authentication is required to access system wallets management",
            )
