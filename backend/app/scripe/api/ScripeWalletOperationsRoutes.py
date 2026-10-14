# /* ../NauTrader_Helm/payments-core/backend/app/scripe/api/ScripeWalletOperationsRoutes.py */
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_current_user
from app.core.db import get_db
from app.core.guards import require_write_access
from app.schemas import TransferCreate
from app.scripe.application.requests.ScripeDepositRequest import ScripeDepositRequest
from app.scripe.application.services.ScripeDepositService import ScripeDepositService
from app.scripe.application.services.ScripeTestDepositService import ScripeTestDepositService
from app.scripe.application.services.ScripeTestResetService import ScripeTestResetService
from app.scripe.application.services.ScripeWalletTransferService import ScripeWalletTransferService


class ScripeWalletOperationsRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/scripe/wallet-operations",
            tags=["scripe-wallet-operations"],
        )
        self.router.add_api_route("/deposit", self.deposit, methods=["POST"], status_code=201)
        self.router.add_api_route("/test-deposit", self.test_deposit, methods=["POST"], status_code=201)
        self.router.add_api_route("/test-reset", self.test_reset, methods=["POST"], status_code=201)
        self.router.add_api_route("/transfer", self.transfer, methods=["POST"], status_code=201)

    def deposit(
        self,
        payload: ScripeDepositRequest,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        return self._adjust(
            request,
            session,
            current_user,
            idempotency_key,
            ScripeDepositService().deposit,
            payload.amount_minor,
        )

    def test_deposit(
        self,
        payload: ScripeDepositRequest,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        return self._adjust(
            request,
            session,
            current_user,
            idempotency_key,
            ScripeTestDepositService().deposit,
            payload.amount_minor,
        )

    def _adjust(
        self,
        request: Request,
        session: Session,
        current_user: AuthenticatedUser,
        idempotency_key: str | None,
        operation,
        amount_minor: int,
    ) -> dict:
        require_write_access(request)
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
        try:
            transaction = operation(
                session,
                owner_id=current_user.id,
                amount_minor=amount_minor,
                idempotency_key=idempotency_key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "transaction_id": str(transaction.id),
            "status": transaction.status.value,
            "currency_code": transaction.currency_code,
            "description": transaction.description,
        }

    def test_reset(
        self,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        require_write_access(request)
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
        try:
            transaction = ScripeTestResetService().reset(
                session,
                owner_id=current_user.id,
                idempotency_key=idempotency_key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "transaction_id": str(transaction.id),
            "status": transaction.status.value,
            "currency_code": transaction.currency_code,
            "description": transaction.description,
        }

    def transfer(
        self,
        payload: TransferCreate,
        request: Request,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict:
        require_write_access(request)
        if not idempotency_key:
            raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
        try:
            result = ScripeWalletTransferService().transfer(
                session,
                owner_id=current_user.id,
                from_account_id=payload.from_account_id,
                to_account_id=payload.to_account_id,
                amount_minor=payload.amount_minor,
                idempotency_key=idempotency_key,
                description=payload.description,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result.payload
