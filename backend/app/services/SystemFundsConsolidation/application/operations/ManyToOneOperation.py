# /* ../NauTrader_Helm/payments-core/backend/app/services/SystemFundsConsolidation/application/operations/ManyToOneOperation.py */
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Account
from app.schemas import TransferCreate
from app.services.balances import account_balances_minor
from app.services.transfers import create_transfer
from app.services.SystemFundsConsolidation.application.services.SystemFundsConsolidationWalletValidator import (
    SystemFundsConsolidationWalletValidator,
)
from app.services.SystemFundsConsolidation.domain.config.ManyToOneConfig import (
    ManyToOneConfig,
)


class ManyToOneOperation:
    @classmethod
    def execute(
        cls,
        session: Session,
        *,
        execution_time: datetime,
    ) -> dict[str, int]:
        if execution_time.tzinfo is None:
            raise ValueError("Execution time must be timezone-aware.")

        config = ManyToOneConfig
        config.validate()
        hour_key = execution_time.astimezone(timezone.utc).strftime("%Y%m%dT%H")
        required_codes = (
            *config.SOURCE_WALLET_CODES,
            config.DESTINATION_WALLET_CODE,
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
            destination = accounts_by_code[config.DESTINATION_WALLET_CODE]
            prelocked_accounts = {
                account.id: account for account in accounts_by_code.values()
            }

            for source_code in config.SOURCE_WALLET_CODES:
                source: Account = accounts_by_code[source_code]
                _posted, _held, available = account_balances_minor(
                    session,
                    source.id,
                )
                if available < config.MINIMUM_TRANSFER_MINOR:
                    continue

                idempotency_key = (
                    f"{config.IDEMPOTENCY_PREFIX}:{source_code}:"
                    f"{config.DESTINATION_WALLET_CODE}:{hour_key}"
                )
                result = create_transfer(
                    session,
                    idempotency_key=idempotency_key,
                    transfer=TransferCreate(
                        from_account_id=source.id,
                        to_account_id=destination.id,
                        amount_minor=available,
                        currency_code=config.CURRENCY_CODE,
                        description=(
                            f"{config.DESCRIPTION_PREFIX} "
                            f"{source_code}->{config.DESTINATION_WALLET_CODE} "
                            f"{hour_key}"
                        ),
                    ),
                    owner_id=source.owner_id,
                    scope=config.IDEMPOTENCY_SCOPE,
                    request_payload={
                        "execution_type": config.EXECUTION_TYPE,
                        "source_wallet": source_code,
                        "destination_wallet": config.DESTINATION_WALLET_CODE,
                        "amount_minor": available,
                        "currency_code": config.CURRENCY_CODE,
                        "execution_hour": hour_key,
                    },
                    commit=False,
                    prelocked_accounts=prelocked_accounts,
                )
                if result.created:
                    transferred[source_code] = available

        return transferred
