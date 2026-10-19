# /* ../NauTrader_Helm/payments-core/backend/app/features/transfers/application/services/TransferMiddleware.py */
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helm.application.services.HelmTariffService import HelmTariffService
from app.features.transfers.domain.models.TransferCommand import TransferCommand
from app.features.transfers.domain.models.TransferResult import TransferResult
from app.core.idempotency import request_hash
from app.models import Account, IdempotencyKey
from app.schemas import TransferCreate
from app.services.transfers import (
    IdempotencyConflictError,
    TransferConflictError,
    TransferValidationError,
    create_transfer,
)


class TransferMiddleware:
    TARIFF_KEY = "scr_transfers_profit_fees"
    DISCOUNT_TARIFF_KEY = "discount_plans"

    def __init__(self, tariff_service: HelmTariffService) -> None:
        self._tariff_service = tariff_service

    def execute(
        self,
        session: Session,
        *,
        command: TransferCommand,
        owner_id: UUID,
        authorization: str,
        idempotency_key: str,
    ) -> TransferResult:
        if not authorization:
            raise HTTPException(status_code=401, detail="Bearer token required")
        if not idempotency_key.strip():
            raise HTTPException(status_code=400, detail="Idempotency-Key is required")

        operation_payload = {
            "owner_id": str(owner_id),
            "command": command.model_dump(mode="json"),
        }
        operation_hash = request_hash("transfer_middleware", operation_payload)
        existing_operation = session.get(IdempotencyKey, idempotency_key)
        if existing_operation is not None:
            if (
                existing_operation.scope != "transfer_middleware"
                or existing_operation.request_hash != operation_hash
            ):
                raise IdempotencyConflictError("IDEMPOTENCY_KEY_REUSED")
            if existing_operation.response_json is None:
                raise TransferValidationError(
                    "Existing middleware idempotency record is incomplete",
                    code="IDEMPOTENCY_INCOMPLETE",
                )
            return TransferResult.model_validate(existing_operation.response_json)

        execution_at = command.execution_at or datetime.now(timezone.utc)
        self._validate_execution_window(command, execution_at)

        source = session.get(Account, command.from_account_id)
        destination = session.get(Account, command.to_account_id)
        if source is None or source.owner_id != owner_id:
            raise TransferValidationError(
                "Source account not found",
                code="ACCOUNT_NOT_FOUND",
            )
        if destination is None:
            raise TransferValidationError(
                "Destination account not found",
                code="ACCOUNT_NOT_FOUND",
            )
        if not source.wallet_code or not destination.wallet_code:
            raise TransferValidationError(
                "Source and destination must have wallet codes",
                code="WALLET_CODE_MISSING",
            )

        tariff = self._tariff_service.get_user_tariff_entity(
            authorization,
            self.TARIFF_KEY,
        )
        percentage = self._resolve_fee_percentage(
            tariff,
            source.wallet_code,
            destination.wallet_code,
        )
        fee_minor = self._calculate_fee(command.amount_minor, percentage)

        discounts_status = self._get_discount_status(
            authorization,
            command.apply_discounts,
        )

        transfer_payload = command.model_dump(mode="json")
        transfer_payload["execution_at"] = execution_at.isoformat()
        base_key = sha256(idempotency_key.encode("utf-8")).hexdigest()
        transfers: list[dict[str, Any]] = []

        try:
            account_ids = {
                command.from_account_id,
                command.to_account_id,
                command.fee_account_id,
            }
            locked_accounts = session.execute(
                select(Account)
                .where(Account.id.in_(account_ids))
                .order_by(Account.wallet_code, Account.id)
                .with_for_update()
            ).scalars().all()
            locked_accounts_by_id = {
                account.id: account for account in locked_accounts
            }
            if set(locked_accounts_by_id) != account_ids:
                raise TransferValidationError(
                    "One or more transfer accounts were not found",
                    code="ACCOUNT_NOT_FOUND",
                )

            fee_account = locked_accounts_by_id[command.fee_account_id]
            if fee_account.owner_id != owner_id:
                raise TransferValidationError(
                    "Fee account not found",
                    code="ACCOUNT_NOT_FOUND",
                )
            if not fee_account.wallet_code:
                raise TransferValidationError(
                    "Fee account must have a wallet code",
                    code="WALLET_CODE_MISSING",
                )
            if (
                command.effective_fee_destination == "recipient"
                and locked_accounts_by_id[command.to_account_id].owner_id != owner_id
            ):
                raise TransferValidationError(
                    "Recipient account not found",
                    code="ACCOUNT_NOT_FOUND",
                )
            main_transfer = TransferCreate(
                from_account_id=command.from_account_id,
                to_account_id=command.to_account_id,
                currency_code=command.currency_code,
                amount_minor=command.amount_minor,
                description=command.description or "Wallet transfer",
            )
            main_result = create_transfer(
                session,
                idempotency_key=f"{base_key}:main",
                transfer=main_transfer,
                owner_id=owner_id,
                scope="transfer_middleware.main",
                request_payload={
                    "command": transfer_payload,
                    "leg": "main",
                    "amount_minor": command.amount_minor,
                },
                commit=False,
                prelocked_accounts=locked_accounts_by_id,
            )
            transfers.append(main_result.payload)

            if fee_minor > 0:
                fee_source_account_id = (
                    command.to_account_id
                    if command.effective_fee_destination == "recipient"
                    else command.from_account_id
                )
                fee_transfer = TransferCreate(
                    from_account_id=fee_source_account_id,
                    to_account_id=command.fee_account_id,
                    currency_code=command.currency_code,
                    amount_minor=fee_minor,
                    description="Wallet transfer fee",
                )
                fee_result = create_transfer(
                    session,
                    idempotency_key=f"{base_key}:fee",
                    transfer=fee_transfer,
                    owner_id=owner_id,
                    scope="transfer_middleware.fee",
                    request_payload={
                        "command": transfer_payload,
                        "leg": "fee",
                        "amount_minor": fee_minor,
                    },
                    commit=False,
                    prelocked_accounts=locked_accounts_by_id,
                )
                transfers.append(fee_result.payload)

            currency_code = command.currency_code or source.currency_code
            result = TransferResult(
                mode=command.mode,
                amount_minor=command.amount_minor,
                fee_minor=fee_minor,
                fee_percentage=percentage,
                currency_code=currency_code,
                execution_at=execution_at,
                discounts_status=discounts_status,
                transfers=transfers,
            )
            session.add(
                IdempotencyKey(
                    key=idempotency_key,
                    scope="transfer_middleware",
                    request_hash=operation_hash,
                    response_json=result.model_dump(mode="json"),
                    status_code=201,
                )
            )
            session.commit()
        except IntegrityError as error:
            session.rollback()
            existing_operation = session.get(IdempotencyKey, idempotency_key)
            if (
                existing_operation is not None
                and existing_operation.scope == "transfer_middleware"
                and existing_operation.request_hash == operation_hash
                and existing_operation.response_json is not None
            ):
                return TransferResult.model_validate(existing_operation.response_json)
            raise IdempotencyConflictError("IDEMPOTENCY_KEY_REUSED") from error
        except Exception:
            session.rollback()
            raise

        return result

    @staticmethod
    def _validate_execution_window(
        command: TransferCommand,
        execution_at: datetime,
    ) -> None:
        if command.valid_from is not None and execution_at < command.valid_from:
            raise TransferValidationError(
                "Execution is before valid_from",
                code="EXECUTION_OUTSIDE_WINDOW",
            )
        if command.valid_until is not None and execution_at > command.valid_until:
            raise TransferValidationError(
                "Execution is after valid_until",
                code="EXECUTION_OUTSIDE_WINDOW",
            )

    @staticmethod
    def _resolve_fee_percentage(
        payload: dict[str, Any],
        from_wallet: str,
        to_wallet: str,
    ) -> Decimal:
        config: Any = payload
        if isinstance(config.get("tariffs"), dict):
            config = config["tariffs"].get(
                TransferMiddleware.TARIFF_KEY,
                config,
            )
        if isinstance(config, dict) and "data" in config:
            config = config["data"]

        if not isinstance(config, dict):
            raise HTTPException(
                status_code=502,
                detail="Invalid transfer tariff response",
            )

        records = config.get("wallet_transfer_fees", [])
        if not isinstance(records, list):
            raise HTTPException(
                status_code=502,
                detail="Invalid wallet_transfer_fees tariff",
            )

        for record in records:
            if not isinstance(record, dict):
                continue
            if (
                record.get("from_wallet") == from_wallet
                and record.get("to_wallet") == to_wallet
            ):
                try:
                    percentage = Decimal(str(record["percentage"]))
                except (KeyError, ArithmeticError, ValueError):
                    break
                if not percentage.is_finite() or not Decimal("0") <= percentage <= Decimal("100"):
                    break
                return percentage

        raise HTTPException(
            status_code=422,
            detail=f"Transfer tariff is not configured for {from_wallet} -> {to_wallet}",
        )

    @staticmethod
    def _calculate_fee(amount_minor: int, percentage: Decimal) -> int:
        fee = (
            Decimal(amount_minor) * percentage / Decimal("100")
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(fee)

    def _get_discount_status(
        self,
        authorization: str,
        apply_discounts: bool,
    ) -> str:
        if not apply_discounts:
            return "disabled_by_request"

        # Discount tariff fields are not yet standardized in Helm.
        # Keep the integration explicit and fail closed until its contract exists.
        try:
            self._tariff_service.get_user_tariff_entity(
                authorization,
                self.DISCOUNT_TARIFF_KEY,
            )
        except HTTPException:
            return "placeholder_unavailable"
        return "placeholder_not_applied"
