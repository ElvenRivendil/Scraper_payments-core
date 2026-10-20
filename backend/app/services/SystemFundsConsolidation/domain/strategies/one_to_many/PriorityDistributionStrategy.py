# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/domain/strategies/one_to_many/PriorityDistributionStrategy.py */
from __future__ import annotations

from app.services.SystemFundsConsolidation.domain.value_objects.DistributionTarget import (
    DistributionTarget,
)


class PriorityDistributionStrategy:
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

        ordered = sorted(targets, key=lambda target: (target.priority, target.wallet_code))
        total_capacity = sum(
            target.max_amount_minor
            if target.max_amount_minor is not None
            else amount_minor
            for target in ordered
        )
        if total_capacity < amount_minor:
            raise ValueError(
                "Configured destination limits cannot absorb the full amount."
            )

        remaining = amount_minor
        allocations = {target.wallet_code: 0 for target in ordered}
        for target in ordered:
            if remaining == 0:
                break
            capacity = (
                target.max_amount_minor
                if target.max_amount_minor is not None
                else remaining
            )
            allocation = min(remaining, capacity)
            allocations[target.wallet_code] = allocation
            remaining -= allocation

        if remaining:
            raise ValueError("Priority strategy did not allocate the full amount.")
        return allocations
