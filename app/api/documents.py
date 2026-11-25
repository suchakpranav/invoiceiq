import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.models import DocumentRow, InvoiceRow
from app.schemas.document import Document, DocumentLink
from app.services.storage import DocumentTooLarge, InvalidDocument, store_document

logger = logging.getLogger(__name__)


def document_router(engine: Engine, root: Path, limit: int) -> APIRouter:
    router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
    sessions = sessionmaker(engine, expire_on_commit=False)
    root = root.resolve()

    def require_invoice(session, invoice_id):
        if invoice_id is not None and session.get(InvoiceRow, str(invoice_id)) is None:
            raise HTTPException(404, "Invoice not found")

    def require_document(session, document_id):
        row = session.get(DocumentRow, str(document_id))
        if row is None:
            raise HTTPException(404, "Document not found")
        return row

    @router.post("", response_model=Document, status_code=201)
    def upload(file: Annotated[UploadFile, File()],
               invoice_id: Annotated[UUID | None, Form()] = None):
        with sessions() as session:
            require_invoice(session, invoice_id)
        try:
            name, key, media, size, digest = store_document(
                file.file, file.filename or "", root, limit
            )
        except DocumentTooLarge as exc:
            raise HTTPException(413, str(exc)) from exc
        except InvalidDocument as exc:
            raise HTTPException(415, str(exc)) from exc
        try:
            with sessions.begin() as session:
                row = DocumentRow(
                    id=str(uuid4()), invoice_id=str(invoice_id) if invoice_id else None,
                    original_filename=name, storage_key=key, content_type=media,
                    size_bytes=size, sha256=digest, uploaded_at=datetime.now(timezone.utc),
                )
                session.add(row)
                session.flush()
                result = Document.model_validate(row)
        except IntegrityError as exc:
            (root / key).unlink(missing_ok=True)
            raise HTTPException(409, "Document metadata conflict") from exc
        except Exception:
            (root / key).unlink(missing_ok=True)
            raise
        return result

    @router.get("", response_model=list[Document])
    def list_documents(invoice_id: UUID | None = None,
                       offset: Annotated[int, Query(ge=0)] = 0,
                       limit: Annotated[int, Query(ge=1, le=100)] = 20):
        with sessions() as session:
            query = select(DocumentRow)
            if invoice_id:
                query = query.where(DocumentRow.invoice_id == str(invoice_id))
            query = query.order_by(DocumentRow.uploaded_at.desc(), DocumentRow.id)
            return [Document.model_validate(row) for row in
                    session.scalars(query.offset(offset).limit(limit))]

    @router.get("/{document_id}", response_model=Document)
    def get_document(document_id: UUID):
        with sessions() as session:
            return Document.model_validate(require_document(session, document_id))

    @router.patch("/{document_id}/invoice", response_model=Document)
    def link_document(document_id: UUID, data: DocumentLink):
        try:
            with sessions.begin() as session:
                row = require_document(session, document_id)
                require_invoice(session, data.invoice_id)
                row.invoice_id = str(data.invoice_id) if data.invoice_id else None
                return Document.model_validate(row)
        except IntegrityError as exc:
            raise HTTPException(409, "Invoice link conflict") from exc

    @router.get("/{document_id}/download")
    def download(document_id: UUID):
        with sessions() as session:
            row = require_document(session, document_id)
            path = root / row.storage_key
            if not path.is_file():
                raise HTTPException(404, "Stored file missing")
            return FileResponse(path, media_type="application/octet-stream",
                                filename=row.original_filename,
                                headers={"X-Content-Type-Options": "nosniff"})

    @router.delete("/{document_id}", status_code=204)
    def delete(document_id: UUID):
        with sessions.begin() as session:
            row = require_document(session, document_id)
            key = row.storage_key
            session.delete(row)
        try:
            (root / key).unlink(missing_ok=True)
        except OSError:
            logger.exception("Orphaned document file: %s", key)
        return Response(status_code=204)

    return router
