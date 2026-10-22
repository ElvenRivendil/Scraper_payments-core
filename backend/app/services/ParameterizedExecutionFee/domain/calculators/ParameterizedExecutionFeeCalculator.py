# /* ../NauTrader_Helm/payments-core/backend/app/services/ParameterizedExecutionFee/domain/calculators/ParameterizedExecutionFeeCalculator.py */

from decimal import Decimal
from collections.abc import Sequence

from app.scripe.domain.value_objects.ScripeAmount import ScripeAmount
from app.services.ParameterizedExecutionFee.domain.models.ExecutionFeeBand import (
    ExecutionFeeBand,
)


class ParameterizedExecutionFeeCalculator:
    @classmethod
    def calculate(
        cls,
        *,
        volume: Decimal,
        bands: Sequence[ExecutionFeeBand],
    ) -> int:
        if not isinstance(volume, Decimal):
            raise TypeError("Position volume must be Decimal.")
        if not volume.is_finite() or volume < 0:
            raise ValueError("Position volume must be finite and non-negative.")
        if not bands:
            raise ValueError("At least one execution fee band is required.")

        ordered_bands = sorted(bands, key=lambda band: band.from_value)
        for band in ordered_bands:
            band.validate()

        if ordered_bands[0].from_value != Decimal("0"):
            raise ValueError("Execution fee bands must start at zero.")

        for index, band in enumerate(ordered_bands):
            is_last = index == len(ordered_bands) - 1
            if is_last:
                if band.to_value is not None:
                    raise ValueError("The last execution fee band must be open-ended.")
                continue

            next_band = ordered_bands[index + 1]
            if band.to_value is None or band.to_value != next_band.from_value:
                raise ValueError("Execution fee bands must be contiguous.")

        matching_bands = [
            band
            for band in ordered_bands
            if band.from_value <= volume
            and (band.to_value is None or volume < band.to_value)
        ]
        if len(matching_bands) != 1:
            raise LookupError("Position volume must match exactly one execution fee band.")

        fee_amount = volume * matching_bands[0].percent / Decimal("100")
        return ScripeAmount.to_minor_units(fee_amount)
