# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/application/operations/ResolveExecutionFeeBandsOperation.py */

from decimal import Decimal, InvalidOperation
from uuid import UUID

from app.api.helm.infrastructure.clients.HelmApiClient import HelmApiClient
from app.services.ParameterizedExecutionFee.domain.models.ExecutionFeeBand import (
    ExecutionFeeBand,
)


class ResolveExecutionFeeBandsOperation:
    MODES = frozenset({"paper", "live", "mock", "backtests"})

    @classmethod
    def execute(
        cls,
        client: HelmApiClient,
        *,
        user_id: UUID,
        mode: str,
        internal_secret: str,
        tariff_entity_key: str,
        percentage_key: str = "profit_percent",
    ) -> tuple[ExecutionFeeBand, ...]:
        if mode not in cls.MODES:
            raise ValueError("Unsupported execution mode.")
        if not isinstance(tariff_entity_key, str) or not tariff_entity_key.strip():
            raise ValueError("Tariff entity key must not be empty.")
        if not isinstance(percentage_key, str) or not percentage_key.strip():
            raise ValueError("Tariff percentage key must not be empty.")

        payload = client.get_internal_user_tariff_entity(
            user_id,
            tariff_entity_key,
            internal_secret,
        )
        items = payload.get("items")
        if not isinstance(items, list):
            raise RuntimeError("Helm returned an invalid tariff items collection.")

        bands: list[ExecutionFeeBand] = []
        for item in items:
            if not isinstance(item, dict) or item.get("mode") != mode:
                continue

            try:
                raw_from = item.get("from_value")
                raw_to = item.get("to_value")
                raw_percent = item.get(percentage_key)
                if raw_from is None or raw_percent is None:
                    raise ValueError
                band = ExecutionFeeBand(
                    band_key=str(item.get("band_key", "")),
                    from_value=Decimal(str(raw_from)),
                    to_value=Decimal(str(raw_to)) if raw_to is not None else None,
                    percent=Decimal(str(raw_percent)),
                )
                band.validate()
            except (InvalidOperation, ValueError, TypeError):
                raise RuntimeError("Helm returned an invalid commission band.") from None
            bands.append(band)

        if not bands:
            raise LookupError("No commission bands found for the requested mode.")

        return tuple(sorted(bands, key=lambda band: band.from_value))
