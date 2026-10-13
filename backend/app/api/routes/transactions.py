from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_current_user
from app.core.db import get_db
from app.schemas import TransactionDetailOut, TransactionOut
from app.services.transactions import get_transaction_detail, list_transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def read_transactions(
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_current_user),
):
    return list_transactions(session, owner_id=current_user.id)


@router.get("/{transaction_id}", response_model=TransactionDetailOut)
def read_transaction(
    transaction_id: UUID,
    session: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(require_current_user),
):
    transaction = get_transaction_detail(session, transaction_id, owner_id=current_user.id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction
