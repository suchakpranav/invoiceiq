from threading import Lock
from uuid import UUID, uuid4

from app.schemas.invoice import Invoice, InvoiceInput


class InvoiceRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, Invoice] = {}
        self._lock = Lock()

    def create(self, data: InvoiceInput) -> Invoice:
        record = Invoice(id=uuid4(), **data.model_dump())
        with self._lock:
            self._records[record.id] = record
        return record

    def get(self, invoice_id: UUID) -> Invoice | None:
        with self._lock:
            return self._records.get(invoice_id)

    def list(self) -> list[Invoice]:
        with self._lock:
            return list(self._records.values())

    def replace(self, invoice_id: UUID, data: InvoiceInput) -> Invoice | None:
        with self._lock:
            if invoice_id not in self._records:
                return None
            record = Invoice(id=invoice_id, **data.model_dump())
            self._records[invoice_id] = record
            return record

    def delete(self, invoice_id: UUID) -> bool:
        with self._lock:
            return self._records.pop(invoice_id, None) is not None
