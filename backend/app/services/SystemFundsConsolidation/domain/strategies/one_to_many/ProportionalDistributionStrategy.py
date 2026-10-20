# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/strategies/one_to_many/ProportionalDistributionStrategy.py */
from __future__ import annotations

from app.services.SystemFundsConsolidation.domain.value_objects.DistributionTarget import (
    DistributionTarget,
)


class ProportionalDistributionStrategy:
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

        total_weight = sum(target.weight for target in targets)
        allocations: dict[str, int] = {}
        remainders: list[tuple[int, int, str]] = []
        allocated = 0

        for index, target in enumerate(targets):
            base, remainder = divmod(
                amount_minor * target.weight,
                total_weight,
            )
            allocations[target.wallet_code] = base
            remainders.append((remainder, -index, target.wallet_code))
            allocated += base

        for _, _, wallet_code in sorted(remainders, reverse=True)[
            : amount_minor - allocated
        ]:
            allocations[wallet_code] += 1

        return allocations
