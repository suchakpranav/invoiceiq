from datetime import date

from sqlalchemy import BigInteger, CheckConstraint, Date, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InvoiceRow(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("subtotal_cents BETWEEN 0 AND 999999999999"),
        CheckConstraint("tax_basis_points BETWEEN 0 AND 10000"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(150))
    supplier: Mapped[str] = mapped_column(String(150), index=True)
    customer: Mapped[str] = mapped_column(String(150))
    invoice_date: Mapped[date] = mapped_column(Date, index=True)
    subtotal_cents: Mapped[int] = mapped_column(BigInteger)
    tax_basis_points: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(500))
