# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/application/services/ParameterizedExecutionFeeService.py */

from decimal import Decimal
from uuid import UUID

from app.services.ParameterizedExecutionFee.application.services.ResolveExecutionFeeBandsService import (
    ResolveExecutionFeeBandsService,
)
from app.services.ParameterizedExecutionFee.domain.calculators.ParameterizedExecutionFeeCalculator import (
    ParameterizedExecutionFeeCalculator,
)
from app.services.ParameterizedExecutionFee.domain.models.ParameterizedExecutionFeeResult import (
    ParameterizedExecutionFeeResult,
)


class ParameterizedExecutionFeeService:
    @classmethod
    def calculate(
        cls,
        *,
        user_id: UUID,
        mode: str,
        volume: Decimal,
        tariff_entity_key: str,
        percentage_key: str = "profit_percent",
    ) -> ParameterizedExecutionFeeResult:
        bands = ResolveExecutionFeeBandsService.resolve(
            user_id=user_id,
            mode=mode,
            tariff_entity_key=tariff_entity_key,
            percentage_key=percentage_key,
        )
        ordered_bands = tuple(sorted(bands, key=lambda band: band.from_value))
        amount_minor = ParameterizedExecutionFeeCalculator.calculate(
            volume=volume,
            bands=ordered_bands,
        )
        selected_band = next(
            (
                band for band in ordered_bands
                if band.from_value <= volume
                and (band.to_value is None or volume < band.to_value)
            ),
            None,
        )
        if selected_band is None:
            raise LookupError("Position volume must match exactly one commission band.")
        return ParameterizedExecutionFeeResult(
            status="calculated" if amount_minor > 0 else "no_fee",
            amount_minor=amount_minor,
            band_key=selected_band.band_key,
            percent=str(selected_band.percent),
        )
