import logging
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.db.models import DocumentRow, ProcessedPageRow
from app.services.processing import ProcessingError, prepare_document

logger = logging.getLogger(__name__)


class PageResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page_number: int
    method: str
    extracted_text: str
    width: int | None
    height: int | None


def processing_router(engine: Engine, root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/documents", tags=["Processing"])
    sessions = sessionmaker(engine)
    root = root.resolve()

    @router.post("/{document_id}/process", response_model=list[PageResult])
    def process(document_id: UUID):
        with sessions.begin() as session:
            row = session.scalar(select(DocumentRow).where(
                DocumentRow.id == str(document_id)).with_for_update())
            if row is None:
                raise HTTPException(404, "Document not found")
            path = root / row.storage_key
            if not path.is_file():
                raise HTTPException(404, "Stored file missing")
            try:
                pages = prepare_document(path, row.content_type)
            except ProcessingError as exc:
                raise HTTPException(422, str(exc)) from exc
            except Exception as exc:
                logger.exception("Document processing failed: %s", document_id)
                raise HTTPException(422, "Unable to process document") from exc
            session.execute(delete(ProcessedPageRow).where(
                ProcessedPageRow.document_id == str(document_id)))
            for page in pages:
                session.add(ProcessedPageRow(document_id=str(document_id), **asdict(page)))
            return [PageResult.model_validate(page) for page in pages]

    @router.get("/{document_id}/pages", response_model=list[PageResult])
    def get_pages(document_id: UUID):
        with sessions() as session:
            if session.get(DocumentRow, str(document_id)) is None:
                raise HTTPException(404, "Document not found")
            query = select(ProcessedPageRow).where(
                ProcessedPageRow.document_id == str(document_id)
            ).order_by(ProcessedPageRow.page_number)
            return [PageResult.model_validate(page) for page in session.scalars(query)]

    @router.get("/{document_id}/pages/{page_number}/image")
    def get_image(document_id: UUID, page_number: int):
        with sessions() as session:
            page = session.get(ProcessedPageRow, (str(document_id), page_number))
            if page is None or page.image_png is None:
                raise HTTPException(404, "Prepared image not found")
            return Response(page.image_png, media_type="image/png",
                            headers={"X-Content-Type-Options": "nosniff"})

    return router
