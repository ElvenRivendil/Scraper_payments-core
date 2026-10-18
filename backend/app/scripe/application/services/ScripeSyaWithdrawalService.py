# /* ../NauTrader_Helm/payments-core/backend/app/scripe/application/services/ScripeSyaWithdrawalService.py */
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.idempotency import request_hash
from app.core.metrics import mark_idempotency_replay
from app.models import Account, IdempotencyKey, ScripeSyaWithdrawalWindow
from app.schemas import TransferCreate
from app.services.balances import account_balances_minor
from app.services.transfers import (
    IdempotencyConflictError,
    TransferConflictError,
    TransferResult,
    TransferValidationError,
    create_transfer,
)


class ScripeSyaWithdrawalUnavailable(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ScripeSyaWithdrawalService:
    IDEMPOTENCY_SCOPE = "scripe.sya-withdrawal"

    def withdraw(
        self,
        session: Session,
        *,
        owner_id: UUID,
        idempotency_key: str,
    ) -> TransferResult:
        request_payload = {
            "owner_id": str(owner_id),
            "operation": "sya_withdrawal_to_er",
        }
        payload_hash = request_hash(self.IDEMPOTENCY_SCOPE, request_payload)

        accounts = session.execute(
            select(Account)
            .where(
                Account.owner_id == owner_id,
                Account.wallet_code.in_(("SYA", "ER")),
            )
            .order_by(Account.wallet_code)
            .with_for_update()
        ).scalars().all()
        accounts_by_code = {account.wallet_code: account for account in accounts}
        source = accounts_by_code.get("SYA")
        destination = accounts_by_code.get("ER")
        if source is None or destination is None:
            raise TransferValidationError(
                "SYA or ER wallet was not found for this user",
                code="ACCOUNT_NOT_FOUND",
            )
        if source.currency_code != "SCR" or destination.currency_code != "SCR":
            raise TransferValidationError(
                "SYA and ER wallets must use SCR currency",
                code="CURRENCY_MISMATCH",
            )

        existing = session.get(IdempotencyKey, idempotency_key)
        if existing is not None:
            if (
                existing.scope != self.IDEMPOTENCY_SCOPE
                or existing.request_hash != payload_hash
            ):
                raise IdempotencyConflictError("IDEMPOTENCY_KEY_REUSED")
            if existing.response_json is None:
                raise TransferValidationError(
                    "Existing idempotency record is incomplete",
                    code="IDEMPOTENCY_INCOMPLETE",
                )
            mark_idempotency_replay()
            return TransferResult(payload=existing.response_json, created=False)

        now = datetime.now(timezone.utc)
        window_start = now.replace(minute=0, second=0, microsecond=0)

        if now.minute < 16:
            raise ScripeSyaWithdrawalUnavailable(
                "WITHDRAWAL_WINDOW_NOT_OPEN",
                "SYA withdrawal is available from minute 16 of each UTC hour",
            )

        used_window = session.get(
            ScripeSyaWithdrawalWindow,
            (owner_id, window_start),
        )
        if used_window is not None:
            raise ScripeSyaWithdrawalUnavailable(
                "WITHDRAWAL_ALREADY_USED",
                "SYA withdrawal has already been used during this UTC hour",
            )

        _posted, _held, available_balance = account_balances_minor(session, source.id)
        if available_balance <= 0:
            raise TransferConflictError(
                "NO_AVAILABLE_BALANCE",
                "SYA has no available balance to withdraw",
                available_balance=available_balance,
                required=1,
            )

        transfer = TransferCreate(
            from_account_id=source.id,
            to_account_id=destination.id,
            currency_code="SCR",
            amount_minor=available_balance,
            description="SYA withdrawal to ER",
        )
        try:
            result = create_transfer(
                session,
                idempotency_key=idempotency_key,
                transfer=transfer,
                owner_id=owner_id,
                scope=self.IDEMPOTENCY_SCOPE,
                request_payload=request_payload,
                commit=False,
            )
            session.add(
                ScripeSyaWithdrawalWindow(
                    owner_id=owner_id,
                    window_start=window_start,
                    idempotency_key=idempotency_key,
                    response_json=result.payload,
                )
            )
            session.commit()
        except IntegrityError as error:
            session.rollback()
            now = datetime.now(timezone.utc)
            window_start = now.replace(minute=0, second=0, microsecond=0)
            existing = session.get(IdempotencyKey, idempotency_key)
            if (
                existing is not None
                and existing.scope == self.IDEMPOTENCY_SCOPE
                and existing.request_hash == payload_hash
                and existing.response_json is not None
            ):
                mark_idempotency_replay()
                return TransferResult(payload=existing.response_json, created=False)
            used_window = session.get(
                ScripeSyaWithdrawalWindow,
                (owner_id, window_start),
            )
            if used_window is not None:
                raise ScripeSyaWithdrawalUnavailable(
                    "WITHDRAWAL_ALREADY_USED",
                    "SYA withdrawal has already been used during this UTC hour",
                ) from error
            raise IdempotencyConflictError("IDEMPOTENCY_KEY_REUSED") from error
        except Exception:
            session.rollback()
            raise
        return result
