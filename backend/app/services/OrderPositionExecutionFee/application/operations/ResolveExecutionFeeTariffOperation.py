# /* ../NauTrader_Helm/payments-core/backend/app/services/OrderPositionExecutionFee/application/operations/ResolveExecutionFeeTariffOperation.py */
from decimal import Decimal, InvalidOperation
from uuid import UUID

from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient
from app.scripe.domain.value_objects.ScripeAmount import ScripeAmount
from app.services.OrderPositionExecutionFee.domain.config.OrderPositionExecutionFeeConfig import (
    OrderPositionExecutionFeeConfig as Config,
)
from app.services.OrderPositionExecutionFee.domain.models.ExecutionFeeTariff import (
    ExecutionFeeTariff,
)


class ResolveExecutionFeeTariffOperation:
    MODES = frozenset({"paper", "live", "mock", "backtests"})
    TARIFF_TYPES = frozenset({"orders", "positions"})

    @classmethod
    def execute(
        cls,
        client: HelmApiClient,
        *,
        user_id: UUID,
        mode: str,
        tariff_type: str,
        internal_secret: str,
    ) -> ExecutionFeeTariff:
        if mode not in cls.MODES:
            raise ValueError("Unsupported execution mode")
        if tariff_type not in cls.TARIFF_TYPES:
            raise ValueError("Unsupported execution fee tariff type")

        payload = client.get_internal_user_tariff_entity(
            user_id,
            Config.TARIFF_ENTITY_KEY,
            internal_secret,
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise RuntimeError("Helm returned an invalid tariff items collection")

        matches = [
            item
            for item in items
            if isinstance(item, dict)
            and item.get("mode") == mode
            and item.get("tariff_type") == tariff_type
        ]
        if len(matches) != 1:
            raise LookupError(
                "Expected exactly one user tariff record for the requested mode and type"
            )

        item = matches[0]
        enabled = item.get("enabled")
        raw_value = item.get("value")
        if not isinstance(enabled, bool):
            raise RuntimeError("Helm returned an invalid tariff enabled flag")
        if isinstance(raw_value, bool) or raw_value is None:
            raise RuntimeError("Helm returned an invalid tariff value")
        try:
            value = Decimal(str(raw_value))
            amount_minor = ScripeAmount.to_minor_units(value)
        except (InvalidOperation, ValueError, TypeError):
            raise RuntimeError("Helm returned an invalid tariff amount") from None
        if amount_minor < 0:
            raise RuntimeError("Helm returned a negative tariff amount")

        return ExecutionFeeTariff(
            mode=mode,
            tariff_type=tariff_type,
            enabled=enabled,
            amount_minor=amount_minor,
        )
