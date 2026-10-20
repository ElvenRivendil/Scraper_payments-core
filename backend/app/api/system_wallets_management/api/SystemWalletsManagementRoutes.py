# /* ../NauTrader_Helm/payments-core/backend/app/api/system_wallets_management/api/SystemWalletsManagementRoutes.py */
from fastapi import APIRouter, Depends, HTTPException, Request

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
from app.api.system_wallets_management.domain.models.SystemWalletsManagementTaskActionResponse import (
    SystemWalletsManagementTaskActionResponse,
)
from app.api.system_wallets_management.domain.models.SystemWalletsManagementTaskStateResponse import (
    SystemWalletsManagementTaskStateResponse,
)
from app.core.auth import AuthenticatedUser, require_current_user
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

    def get_config(
        self,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
    ) -> SystemWalletsManagementConfigResponse:
        self._require_real_user(request, current_user)
        self.policy.require_access(current_user)
        return self.service.get_config()

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
            message="Task settings updated",
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
