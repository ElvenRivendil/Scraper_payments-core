# /* ../NauTrader_Helm/payments-core/backend/app/scripe/api/ScripeSyaWithdrawalRoutes.py */
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_current_user
from app.core.db import get_db
from app.core.guards import require_write_access
from app.scripe.application.services.ScripeSyaWithdrawalService import (
    ScripeSyaWithdrawalService,
    ScripeSyaWithdrawalUnavailable,
)
from app.services.transfers import (
    IdempotencyConflictError,
    TransferConflictError,
    TransferValidationError,
)


class ScripeSyaWithdrawalRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/scripe/wallet-operations",
            tags=["scripe-wallet-operations"],
        )
        self.router.add_api_route(
            "/sya-withdrawal",
            self.withdraw,
            methods=["POST"],
            status_code=201,
        )

    def withdraw(
        self,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        require_write_access(request)
        if not idempotency_key:
            raise HTTPException(
                status_code=400,
                detail="Idempotency-Key header is required",
            )
        try:
            result = ScripeSyaWithdrawalService().withdraw(
                session,
                owner_id=current_user.id,
                idempotency_key=idempotency_key,
            )
        except ScripeSyaWithdrawalUnavailable as exc:
            raise HTTPException(
                status_code=409,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc
        except TransferConflictError as exc:
            raise HTTPException(
                status_code=409,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc
        except IdempotencyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except TransferValidationError as exc:
            raise HTTPException(
                status_code=400,
                detail={"code": exc.code, "message": str(exc)},
            ) from exc
        return result.payload
