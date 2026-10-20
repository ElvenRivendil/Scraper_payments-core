# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/value_objects/DistributionTarget.py */
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DistributionTarget:
    wallet_code: str
    weight: int = 1
    priority: int = 0
    max_amount_minor: int | None = None

    def __post_init__(self) -> None:
        if not self.wallet_code:
            raise ValueError("Destination wallet code must not be empty.")
        if self.weight < 1:
            raise ValueError("Distribution weight must be positive.")
        if self.max_amount_minor is not None and self.max_amount_minor < 1:
            raise ValueError("Maximum allocation must be positive.")
