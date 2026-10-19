# /* ../NauTrader_Helm/payments-core/backend/app/features/transfers/api/TransferRoutes.py */
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.helm.application.services.HelmTariffService import HelmTariffService
from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient
from app.core.auth import AuthenticatedUser, require_current_user
from app.core.db import get_db
from app.core.guards import require_write_access
from app.features.transfers.application.services.TransferMiddleware import TransferMiddleware
from app.features.transfers.domain.models.TransferCommand import TransferCommand
from app.services.transfers import (
    IdempotencyConflictError,
    TransferConflictError,
    TransferValidationError,
)


class TransferRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/transfer-middleware",
            tags=["transfer-middleware"],
        )
        self.router.add_api_route(
            "",
            self.post_transfer,
            methods=["POST"],
            status_code=201,
        )

    def post_transfer(
        self,
        command: TransferCommand,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
        idempotency_key: str | None = Header(
            default=None,
            alias="Idempotency-Key",
        ),
    ):
        require_write_access(request)
        if not idempotency_key:
            raise HTTPException(
                status_code=400,
                detail="Idempotency-Key header is required",
            )

        settings = request.app.state.settings
        tariff_service = HelmTariffService(
            HelmApiClient(base_url=settings.helm_auth_base_url)
        )
        middleware = TransferMiddleware(tariff_service)

        try:
            result = middleware.execute(
                session,
                command=command,
                owner_id=current_user.id,
                authorization=request.headers.get("authorization", ""),
                idempotency_key=idempotency_key,
            )
        except IdempotencyConflictError as error:
            return JSONResponse(
                status_code=409,
                content={
                    "code": "IDEMPOTENCY_KEY_REUSED",
                    "message": str(error),
                },
            )
        except TransferConflictError as error:
            return JSONResponse(
                status_code=409,
                content={
                    "code": error.code,
                    "message": str(error),
                    "available_balance": error.available_balance,
                    "required": error.required,
                },
            )
        except TransferValidationError as error:
            if error.code == "ACCOUNT_NOT_FOUND":
                status_code = 404
            elif error.code in {"CURRENCY_MISMATCH", "EXECUTION_OUTSIDE_WINDOW"}:
                status_code = 409
            else:
                status_code = 400
            return JSONResponse(
                status_code=status_code,
                content={
                    "code": error.code,
                    "message": str(error),
                },
            )

        return result.model_dump(mode="json")
