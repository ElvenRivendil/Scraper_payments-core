# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/strategies/one_to_many/DistributionStrategy.py */
from __future__ import annotations

from typing import Protocol

from app.services.SystemFundsConsolidation.domain.value_objects.DistributionTarget import (
    DistributionTarget,
)


class DistributionStrategy(Protocol):
    def allocate(
        self,
        amount_minor: int,
        targets: tuple[DistributionTarget, ...],
    ) -> dict[str, int]:
        """Return a complete allocation plan without performing transfers."""
        ...
