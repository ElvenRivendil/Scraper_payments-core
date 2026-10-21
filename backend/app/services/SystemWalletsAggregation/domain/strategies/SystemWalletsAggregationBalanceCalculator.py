# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsAggregation/domain/strategies/SystemWalletsAggregationBalanceCalculator.py */

from collections.abc import Mapping
from uuid import UUID


class SystemWalletsAggregationBalanceCalculator:
    @classmethod
    def calculate(
        cls,
        snapshot: Mapping[UUID, tuple[int, int, int]],
    ) -> int:
        total_available_minor = 0

        for user_id, balances in snapshot.items():
            if len(balances) != 3:
                raise ValueError(
                    f"Invalid balance snapshot for user {user_id}."
                )

            posted_minor, held_minor, available_minor = balances
            if any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in balances
            ):
                raise ValueError(
                    f"Balance values must be integers for user {user_id}."
                )
            if available_minor != posted_minor - held_minor:
                raise ValueError(
                    f"Inconsistent balance snapshot for user {user_id}."
                )
            if available_minor < 0:
                raise ValueError(
                    f"Available balance must not be negative for user {user_id}."
                )

            total_available_minor += available_minor

        return total_available_minor
