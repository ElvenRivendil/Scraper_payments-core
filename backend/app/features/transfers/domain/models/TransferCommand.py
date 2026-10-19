# /* ../NauTrader_Helm/payments-core/backend/app/features/transfers/domain/models/TransferCommand.py */
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class TransferCommand(BaseModel):
    from_account_id: UUID
    to_account_id: UUID
    fee_account_id: UUID | None = None
    fee_destination: Literal["recipient", "account"] | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    amount_minor: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=500)
    execution_at: datetime | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    apply_discounts: bool = True

    @model_validator(mode="after")
    def validate_accounts_and_time_window(self) -> "TransferCommand":
        if self.from_account_id == self.to_account_id:
            raise ValueError("Source and destination accounts must differ")
        if self.fee_account_id is not None:
            if self.fee_account_id in {
                self.from_account_id,
                self.to_account_id,
            }:
                raise ValueError("Fee account must differ from source and destination")
        if self.fee_account_id is None:
            raise ValueError("fee_account_id is required for fee collection")
        if (
            self.valid_from is not None
            and self.valid_until is not None
            and self.valid_from > self.valid_until
        ):
            raise ValueError("valid_from must not be later than valid_until")
        for value in (self.execution_at, self.valid_from, self.valid_until):
            if value is not None and value.utcoffset() is None:
                raise ValueError("Execution timestamps must include a timezone")
        return self

    @property
    def effective_fee_destination(self) -> str:
        if self.fee_destination is not None:
            return self.fee_destination
        return "account" if self.fee_account_id is not None else "recipient"

    @property
    def mode(self) -> str:
        return (
            "transfer_with_fee"
            if self.effective_fee_destination == "account"
            else "transfer_with_recipient_fee"
        )
