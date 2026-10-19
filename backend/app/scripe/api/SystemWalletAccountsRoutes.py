# /* ../NauTrader_Helm/payments-core/backend/app/scripe/api/SystemWalletAccountsRoutes.py */
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_current_user
from app.core.authorization.SystemWalletAccessPolicy import SystemWalletAccessPolicy
from app.core.db import get_db
from app.schemas import AccountDetailOut, AccountOut, AccountStatementOut
from app.scripe.application.services.SystemWalletAccountsService import SystemWalletAccountsService


class SystemWalletAccountsRoutes:
    def __init__(self) -> None:
        self.router = APIRouter(
            prefix="/admin/system-wallets",
            tags=["admin-system-wallets"],
        )
        self.policy = SystemWalletAccessPolicy()
        self.service = SystemWalletAccountsService()
        self.router.add_api_route(
            "",
            self.list_accounts,
            methods=["GET"],
            response_model=list[AccountOut],
        )
        self.router.add_api_route(
            "/{account_id}",
            self.get_account,
            methods=["GET"],
            response_model=AccountDetailOut,
        )
        self.router.add_api_route(
            "/{account_id}/statement",
            self.get_statement,
            methods=["GET"],
            response_model=AccountStatementOut,
        )

    def list_accounts(
        self,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
    ) -> list[dict]:
        self.policy.require_access(current_user)
        return self.service.list_accounts(session)

    def get_account(
        self,
        account_id: UUID,
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
    ) -> dict:
        self.policy.require_access(current_user)
        account = self.service.get_account(session, account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="System account not found")
        return account

    def get_statement(
        self,
        account_id: UUID,
        limit: int = Query(default=50, ge=1, le=200),
        current_user: AuthenticatedUser = Depends(require_current_user),
        session: Session = Depends(get_db),
    ) -> dict:
        self.policy.require_access(current_user)
        statement = self.service.get_statement(session, account_id, limit)
        if statement is None:
            raise HTTPException(status_code=404, detail="System account not found")
        return statement
