from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
Rate = Annotated[Decimal, Field(ge=0, le=100, decimal_places=2)]


class InvoiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invoice_number: Name
    supplier: Name
    customer: Name
    invoice_date: date
    subtotal: Money
    tax_rate: Rate = Decimal("0")


class Invoice(InvoiceInput):
    id: UUID

    @computed_field
    @property
    def tax_amount(self) -> Decimal:
        return (self.subtotal * self.tax_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @computed_field
    @property
    def total(self) -> Decimal:
        return (self.subtotal + self.tax_amount).quantize(Decimal("0.01"))


class InvoicePage(BaseModel):
    items: list[Invoice]
    total: int
    offset: int
    limit: int
