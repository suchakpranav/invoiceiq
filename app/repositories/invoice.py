from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.db.models import InvoiceRow
from app.schemas.invoice import Invoice, InvoiceInput, InvoicePage


def row_values(data: InvoiceInput) -> dict:
    values = data.model_dump(exclude={"subtotal", "tax_rate"})
    return {
        **values,
        "subtotal_cents": int(data.subtotal * 100),
        "tax_basis_points": int(data.tax_rate * 100),
    }


def to_invoice(row: InvoiceRow) -> Invoice:
    return Invoice(
        id=UUID(row.id), invoice_number=row.invoice_number,
        supplier=row.supplier, customer=row.customer, invoice_date=row.invoice_date,
        subtotal=Decimal(row.subtotal_cents).scaleb(-2),
        tax_rate=Decimal(row.tax_basis_points).scaleb(-2), notes=row.notes,
    )


class InvoiceRepository:
    def __init__(self, engine: Engine) -> None:
        self.sessions = sessionmaker(engine, expire_on_commit=False)

    def create(self, data: InvoiceInput) -> Invoice:
        with self.sessions.begin() as session:
            row = InvoiceRow(id=str(uuid4()), **row_values(data))
            session.add(row)
            return to_invoice(row)

    def get(self, invoice_id: UUID) -> Invoice | None:
        with self.sessions() as session:
            row = session.get(InvoiceRow, str(invoice_id))
            return to_invoice(row) if row else None

    def list(
        self, q: str, supplier: str, date_from: date | None,
        date_to: date | None, offset: int, limit: int,
    ) -> InvoicePage:
        filters = []
        if q.strip():
            filters.append(or_(*(
                column.icontains(q.strip(), autoescape=True)
                for column in (InvoiceRow.invoice_number, InvoiceRow.supplier, InvoiceRow.customer)
            )))
        if supplier.strip():
            filters.append(InvoiceRow.supplier.icontains(supplier.strip(), autoescape=True))
        if date_from is not None:
            filters.append(InvoiceRow.invoice_date >= date_from)
        if date_to is not None:
            filters.append(InvoiceRow.invoice_date <= date_to)
        with self.sessions() as session:
            total = session.scalar(select(func.count()).select_from(InvoiceRow).where(*filters))
            statement = (
                select(InvoiceRow).where(*filters)
                .order_by(InvoiceRow.invoice_date.desc(), InvoiceRow.id.desc())
                .offset(offset).limit(limit)
            )
            return InvoicePage(
                items=[to_invoice(row) for row in session.scalars(statement)],
                total=total or 0, offset=offset, limit=limit,
            )

    def replace(self, invoice_id: UUID, data: InvoiceInput) -> Invoice | None:
        with self.sessions.begin() as session:
            row = session.get(InvoiceRow, str(invoice_id))
            if row is None:
                return None
            for key, value in row_values(data).items():
                setattr(row, key, value)
            return to_invoice(row)

    def delete(self, invoice_id: UUID) -> bool:
        with self.sessions.begin() as session:
            row = session.get(InvoiceRow, str(invoice_id))
            if row is None:
                return False
            session.delete(row)
            return True
