# /* ../NauTrader_Helm/payments-core/backend/app/services/ExecutionFee/application/services/ExecutionFeeConfirmationService.py */
from collections.abc import Callable
from sqlalchemy.orm import Session
from app.models import IdempotencyKey
from app.services.transfers import (
    IdempotencyConflictError,
    TransferValidationError,
)
from app.services.ExecutionFee.domain.models.ExecutionFeeResult import (
    ExecutionFeeResult,
)


class ExecutionFeeConfirmationService:
    @classmethod
    def confirm(
        cls,
        session: Session,
        *,
        idempotency_key: str,
        idempotency_scope: str,
        execute_fee: Callable[[int], ExecutionFeeResult],
        resolve_tariff: Callable[[], tuple[bool, int]] | None = None,
        prepared_amount_minor: int | None = None,
        prepared_tariff_enabled: bool | None = None,
        is_protective_order: bool = False,
    ) -> ExecutionFeeResult:
        if not idempotency_key.strip():
            raise ValueError("Idempotency key must not be empty.")
        if not idempotency_scope.strip():
            raise ValueError("Idempotency scope must not be empty.")

        existing = session.get(IdempotencyKey, idempotency_key)
        if existing is not None:
            if existing.scope != idempotency_scope:
                raise IdempotencyConflictError("IDEMPOTENCY_KEY_REUSED")
            if existing.response_json is None:
                raise TransferValidationError(
                    "Existing idempotency record is incomplete.",
                    code="IDEMPOTENCY_INCOMPLETE",
                )
            amount_minor = cls._extract_amount_minor(
                existing.response_json,
                expected_idempotency_key=idempotency_key,
            )
            return ExecutionFeeResult(
                status="already_processed",
                amount_minor=amount_minor,
                created=False,
                transaction=existing.response_json,
            )

        if is_protective_order:
            return ExecutionFeeResult(
                status="protective_order_no_fee",
                amount_minor=0,
                created=False,
            )

        if prepared_amount_minor is None:
            if resolve_tariff is None:
                raise ValueError(
                    "Tariff resolver is required when no preparation exists."
                )
            tariff_enabled, amount_minor = resolve_tariff()
        else:
            if prepared_tariff_enabled is None:
                raise ValueError(
                    "Prepared tariff state must include the enabled flag."
                )
            tariff_enabled = prepared_tariff_enabled
            amount_minor = prepared_amount_minor

        if not isinstance(tariff_enabled, bool):
            raise TypeError("Tariff enabled state must be boolean.")
        if isinstance(amount_minor, bool) or not isinstance(amount_minor, int):
            raise TypeError("Execution fee amount must be an integer.")
        if amount_minor < 0:
            raise ValueError("Execution fee amount must not be negative.")

        if not tariff_enabled:
            return ExecutionFeeResult(
                status="tariff_disabled",
                amount_minor=0,
                created=False,
            )

        if amount_minor == 0:
            return ExecutionFeeResult(
                status="no_fee",
                amount_minor=0,
                created=False,
            )

        return execute_fee(amount_minor)

    @staticmethod
    def _extract_amount_minor(
        payload: dict,
        *,
        expected_idempotency_key: str,
    ) -> int:
        if payload.get("idempotency_key") != expected_idempotency_key:
            raise TransferValidationError(
                "Existing transfer result has a mismatched idempotency key.",
                code="IDEMPOTENCY_INCOMPLETE",
            )

        if not payload.get("id"):
            raise TransferValidationError(
                "Existing transfer result has no transaction ID.",
                code="IDEMPOTENCY_INCOMPLETE",
            )

        if payload.get("status") != "POSTED":
            raise TransferValidationError(
                "Existing transfer result is not posted.",
                code="IDEMPOTENCY_INCOMPLETE",
            )

        ledger_entries = payload.get("ledger_entries")
        if not isinstance(ledger_entries, list) or len(ledger_entries) != 2:
            raise TransferValidationError(
                "Existing transfer result has invalid ledger entries.",
                code="IDEMPOTENCY_INCOMPLETE",
            )

        amounts = [entry.get("amount_minor") for entry in ledger_entries]
        if any(
            isinstance(amount, bool)
            or not isinstance(amount, int)
            or amount <= 0
            for amount in amounts
        ) or amounts[0] != amounts[1]:
            raise TransferValidationError(
                "Existing transfer result has inconsistent amounts.",
                code="IDEMPOTENCY_INCOMPLETE",
            )

        return amounts[0]
