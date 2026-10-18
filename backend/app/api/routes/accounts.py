from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_current_user
from app.core.db import get_db
from app.core.guards import require_write_access
from app.schemas import AccountDetailOut, AccountOut, AccountStatementOut
from app.services.accounts import get_account, get_account_statement, list_accounts

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def read_accounts(session: Session = Depends(get_db), current_user: AuthenticatedUser = Depends(require_current_user)):
    return list_accounts(
        session,
        current_user.id,
        effective_role=current_user.effective_role,
    )


@router.post("", status_code=403)
def post_account(request: Request):
    require_write_access(request)
    raise HTTPException(
        status_code=403,
        detail={
            "code": "ACCOUNT_CREATION_DISABLED",
            "message": "Account creation is managed by the system",
        },
    )


@router.get("/{account_id}", response_model=AccountDetailOut)
def read_account(account_id: UUID, session: Session = Depends(get_db), current_user: AuthenticatedUser = Depends(require_current_user)):
    account = get_account(
        session,
        account_id,
        current_user.id,
        effective_role=current_user.effective_role,
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/{account_id}/statement", response_model=AccountStatementOut)
def read_account_statement(account_id: UUID, limit: int = 50, session: Session = Depends(get_db), current_user: AuthenticatedUser = Depends(require_current_user)):
    statement = get_account_statement(
        session,
        account_id,
        owner_id=current_user.id,
        limit=limit,
        effective_role=current_user.effective_role,
    )
    if statement is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return statement
