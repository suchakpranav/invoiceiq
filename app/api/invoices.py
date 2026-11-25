from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response

from app.repositories.invoice import InvoiceRepository
from app.schemas.invoice import Invoice, InvoiceInput, InvoicePage


def invoice_router(repository: InvoiceRepository) -> APIRouter:
    router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

    @router.post("", response_model=Invoice, status_code=201)
    def create_invoice(data: InvoiceInput) -> Invoice:
        return repository.create(data)

    @router.get("", response_model=InvoicePage)
    def list_invoices(
        q: Annotated[str, Query(max_length=150)] = "",
        supplier: Annotated[str, Query(max_length=150)] = "",
        date_from: date | None = None,
        date_to: date | None = None,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> InvoicePage:
        if date_from and date_to and date_from > date_to:
            raise HTTPException(422, "date_from must not exceed date_to")
        records = repository.list()
        term = q.strip().casefold()
        records = [
            r for r in records
            if any(term in value.casefold() for value in (
                r.invoice_number, r.supplier, r.customer
            ))
            and supplier.strip().casefold() in r.supplier.casefold()
            and (date_from is None or r.invoice_date >= date_from)
            and (date_to is None or r.invoice_date <= date_to)
        ]
        records.sort(key=lambda r: (r.invoice_date, str(r.id)), reverse=True)
        return InvoicePage(
            items=records[offset:offset + limit], total=len(records), offset=offset, limit=limit
        )

    @router.get("/{invoice_id}", response_model=Invoice)
    def get_invoice(invoice_id: UUID) -> Invoice:
        record = repository.get(invoice_id)
        if record is None:
            raise HTTPException(404, "Invoice not found")
        return record

    @router.put("/{invoice_id}", response_model=Invoice)
    def replace_invoice(invoice_id: UUID, data: InvoiceInput) -> Invoice:
        record = repository.replace(invoice_id, data)
        if record is None:
            raise HTTPException(404, "Invoice not found")
        return record

    @router.delete("/{invoice_id}", status_code=204)
    def delete_invoice(invoice_id: UUID) -> Response:
        if not repository.delete(invoice_id):
            raise HTTPException(404, "Invoice not found")
        return Response(status_code=204)

    return router
