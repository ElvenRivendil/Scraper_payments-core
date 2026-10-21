# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemWalletsDistributionToSya/domain/strategies/SystemWalletsDistributionToSyaAllocationCalculator.py */

from uuid import UUID


class SystemWalletsDistributionToSyaAllocationCalculator:
    @staticmethod
    def calculate(
        user_balances_minor: dict[UUID, tuple[int, int, int]],
        distribution_amount_minor: int,
    ) -> dict[str, object]:
        if isinstance(distribution_amount_minor, bool) or not isinstance(distribution_amount_minor, int):
            raise ValueError("Distribution amount must be an integer.")
        if distribution_amount_minor < 0:
            raise ValueError("Distribution amount must not be negative.")
        if not user_balances_minor:
            if distribution_amount_minor:
                raise ValueError("Cannot distribute funds without active users.")
            return {
                "er_total_minor": 0,
                "allocations_minor": {},
                "users_with_positive_balance": 0,
            }
        normalized_balances: dict[UUID, int] = {}
        for owner_id, balances in user_balances_minor.items():
            if len(balances) != 3:
                raise ValueError("Each user balance must contain three values.")
            available_balance = balances[2]
            if isinstance(available_balance, bool) or not isinstance(available_balance, int):
                raise ValueError("Available balances must be integers.")
            if available_balance < 0:
                raise ValueError("Available ER balances must not be negative.")
            normalized_balances[owner_id] = available_balance
        er_total_minor = sum(normalized_balances.values())
        if er_total_minor == 0:
            if distribution_amount_minor:
                raise ValueError("Cannot distribute funds when the ER total is zero.")
            return {
                "er_total_minor": 0,
                "allocations_minor": {owner_id: 0 for owner_id in sorted(normalized_balances, key=str)},
                "users_with_positive_balance": 0,
            }
        allocations_minor: dict[UUID, int] = {}
        remainders: list[tuple[int, str, UUID]] = []
        allocated_minor = 0
        for owner_id in sorted(normalized_balances, key=str):
            allocation_minor, remainder = divmod(
                distribution_amount_minor * normalized_balances[owner_id],
                er_total_minor,
            )
            allocations_minor[owner_id] = allocation_minor
            remainders.append((remainder, str(owner_id), owner_id))
            allocated_minor += allocation_minor
        remaining_minor = distribution_amount_minor - allocated_minor
        ordered_remainders = sorted(remainders, key=lambda item: (-item[0], item[1]))
        for _, _, owner_id in ordered_remainders[:remaining_minor]:
            allocations_minor[owner_id] += 1
        if sum(allocations_minor.values()) != distribution_amount_minor:
            raise ValueError("Allocation total does not match the distribution amount.")
        return {
            "er_total_minor": er_total_minor,
            "allocations_minor": allocations_minor,
            "users_with_positive_balance": sum(
                balance_minor > 0
                for balance_minor in normalized_balances.values()
            ),
        }
