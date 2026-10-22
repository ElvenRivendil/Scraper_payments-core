# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/domain/models/ExecutionFeeBand.py */

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExecutionFeeBand:
    band_key: str
    from_value: Decimal
    to_value: Decimal | None
    percent: Decimal

    def validate(self) -> None:
        if not isinstance(self.band_key, str) or not self.band_key.strip():
            raise ValueError("Execution fee band key must be a non-empty string.")
        if not isinstance(self.from_value, Decimal):
            raise TypeError("Execution fee band lower bound must be Decimal.")
        if not self.from_value.is_finite() or self.from_value < 0:
            raise ValueError("Execution fee band lower bound must be finite and non-negative.")
        if self.to_value is not None:
            if not isinstance(self.to_value, Decimal):
                raise TypeError("Execution fee band upper bound must be Decimal or None.")
            if not self.to_value.is_finite() or self.to_value <= self.from_value:
                raise ValueError("Execution fee band upper bound must exceed lower bound.")
        if not isinstance(self.percent, Decimal):
            raise TypeError("Execution fee band percentage must be Decimal.")
        if not self.percent.is_finite() or not Decimal("0") <= self.percent <= Decimal("100"):
            raise ValueError("Execution fee band percentage must be between 0 and 100.")
