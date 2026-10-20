# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/strategies/one_to_many/EqualDistributionStrategy.py */
from __future__ import annotations

from app.services.SystemFundsConsolidation.domain.value_objects.DistributionTarget import (
    DistributionTarget,
)


class EqualDistributionStrategy:
    def allocate(
        self,
        amount_minor: int,
        targets: tuple[DistributionTarget, ...],
    ) -> dict[str, int]:
        if amount_minor < 0 or not targets:
            raise ValueError("A non-negative amount and targets are required.")
        codes = tuple(target.wallet_code for target in targets)
        if len(codes) != len(set(codes)):
            raise ValueError("Destination wallet codes must be unique.")

        quotient, remainder = divmod(amount_minor, len(targets))
        return {
            target.wallet_code: quotient + (index < remainder)
            for index, target in enumerate(targets)
        }
