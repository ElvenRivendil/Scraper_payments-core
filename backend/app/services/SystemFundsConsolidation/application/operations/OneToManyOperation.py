# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/application/operations/OneToManyOperation.py */
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.schemas import TransferCreate
from app.services.balances import account_balances_minor
from app.services.transfers import create_transfer
from app.services.SystemFundsConsolidation.application.services.SystemFundsConsolidationWalletValidator import (
    SystemFundsConsolidationWalletValidator,
)
from app.services.SystemFundsConsolidation.domain.config.OneToManyConfig import (
    OneToManyConfig,
)
from app.services.SystemFundsConsolidation.domain.value_objects.DistributionTarget import (
    DistributionTarget,
)


class OneToManyOperation:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        execution_time: datetime,
        config_class=OneToManyConfig,
    ) -> dict[str, int]:
        if execution_time.tzinfo is None:
            raise ValueError("Execution time must be timezone-aware.")

        config = config_class
        config.validate()
        hour_key = execution_time.astimezone(timezone.utc).strftime("%Y%m%dT%H")
        required_codes = (
            config.SOURCE_WALLET_CODE,
            *config.DESTINATION_WALLET_CODES,
        )
        transferred: dict[str, int] = {}

        with session.begin():
            accounts_by_code = (
                SystemFundsConsolidationWalletValidator.lock_required_wallets(
                    session,
                    required_codes,
                    currency_code=config.CURRENCY_CODE,
                )
            )
            source = accounts_by_code[config.SOURCE_WALLET_CODE]
            prelocked_accounts = {
                account.id: account for account in accounts_by_code.values()
            }
            _posted, _held, available = account_balances_minor(session, source.id)

            if available < config.MINIMUM_TRANSFER_MINOR:
                return transferred

            targets = tuple(
                DistributionTarget(
                    wallet_code=code,
                    weight=config.DESTINATION_WEIGHTS[code],
                    priority=config.DESTINATION_PRIORITIES[code],
                    max_amount_minor=config.DESTINATION_MAX_AMOUNTS_MINOR.get(code),
                )
                for code in config.DESTINATION_WALLET_CODES
                if config.DESTINATION_WEIGHTS[code] > 0
            )
            strategy = config.DISTRIBUTION_STRATEGY()
            allocations = {
                code: 0
                for code in config.DESTINATION_WALLET_CODES
            }
            allocations.update(strategy.allocate(available, targets))

            if set(allocations) != set(config.DESTINATION_WALLET_CODES):
                raise ValueError("Distribution strategy returned unexpected destinations.")
            if any(
                not isinstance(amount, int) or amount < 0
                for amount in allocations.values()
            ):
                raise ValueError("Distribution strategy returned invalid amounts.")
            if sum(allocations.values()) != available:
                raise ValueError("Distribution strategy must allocate the full balance.")

            for destination_code in config.DESTINATION_WALLET_CODES:
                amount = allocations[destination_code]
                if amount < config.MINIMUM_TRANSFER_MINOR:
                    if amount:
                        raise ValueError(
                            f"Allocation for {destination_code} is below the minimum."
                        )
                    continue

                destination = accounts_by_code[destination_code]
                result = create_transfer(
                    session,
                    idempotency_key=(
                        f"{config.IDEMPOTENCY_PREFIX}:{config.SOURCE_WALLET_CODE}:"
                        f"{destination_code}:{hour_key}"
                    ),
                    transfer=TransferCreate(
                        from_account_id=source.id,
                        to_account_id=destination.id,
                        amount_minor=amount,
                        currency_code=config.CURRENCY_CODE,
                        description=(
                            f"{config.DESCRIPTION_PREFIX} "
                            f"{config.SOURCE_WALLET_CODE}->{destination_code} "
                            f"{hour_key}"
                        ),
                    ),
                    owner_id=source.owner_id,
                    scope=config.IDEMPOTENCY_SCOPE,
                    request_payload={
                        "execution_type": config.EXECUTION_TYPE,
                        "strategy": type(strategy).__name__,
                        "source_wallet": config.SOURCE_WALLET_CODE,
                        "destination_wallet": destination_code,
                        "amount_minor": amount,
                        "currency_code": config.CURRENCY_CODE,
                        "execution_hour": hour_key,
                    },
                    commit=False,
                    prelocked_accounts=prelocked_accounts,
                )
                if result.created:
                    transferred[destination_code] = amount

        return transferred
