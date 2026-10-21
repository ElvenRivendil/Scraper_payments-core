# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/domain/models/ExecutionFeeScenario.py */

from dataclasses import dataclass
from typing import Protocol

from app.services.transfers import TransferConflictError


class InsufficientFundsPolicy(Protocol):
    def handle(self, error: TransferConflictError) -> bool:
        ...


@dataclass(frozen=True, slots=True)
class ExecutionFeeScenario:
    tariff_key: str
    destination_wallet_code: str
    idempotency_scope: str
    idempotency_prefix: str
    description_prefix: str
    insufficient_funds_policy: InsufficientFundsPolicy

    def validate(self) -> None:
        values = (
            self.tariff_key,
            self.destination_wallet_code,
            self.idempotency_scope,
            self.idempotency_prefix,
            self.description_prefix,
        )
        if any(not value for value in values):
            raise ValueError("Execution fee scenario settings must not be empty.")
