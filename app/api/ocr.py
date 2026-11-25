from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.models import DocumentRow, OCRPageRow, ProcessedPageRow
from app.services.ocr import OCRError, OCRResult, recognize


class PageOCR(OCRResult):
    page_number: int
    method: str


def ocr_router(engine: Engine, settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/api/v1/documents", tags=["OCR"])
    sessions = sessionmaker(engine)

    def results(session, document_id):
        pages = session.scalars(select(ProcessedPageRow).where(
            ProcessedPageRow.document_id == document_id
        ).order_by(ProcessedPageRow.page_number))
        output = []
        for page in pages:
            if page.method == "embedded_text":
                output.append(PageOCR(page_number=page.page_number, method=page.method,
                                      text=page.extracted_text, words=[], mean_confidence=None))
            else:
                row = session.get(OCRPageRow, (document_id, page.page_number))
                if row is not None:
                    output.append(PageOCR(page_number=page.page_number, method="ocr",
                                          text=row.text, words=row.words,
                                          mean_confidence=row.mean_confidence))
        return output

    @router.post("/{document_id}/ocr", response_model=list[PageOCR])
    def run_ocr(document_id: UUID):
        key = str(document_id)
        with sessions.begin() as session:
            doc = session.scalar(select(DocumentRow).where(
                DocumentRow.id == key).with_for_update())
            if doc is None:
                raise HTTPException(404, "Document not found")
            pages = list(session.scalars(select(ProcessedPageRow).where(
                ProcessedPageRow.document_id == key).order_by(ProcessedPageRow.page_number)))
            if not pages:
                raise HTTPException(409, "Process document first")
            session.execute(delete(OCRPageRow).where(OCRPageRow.document_id == key))
            for page in pages:
                if page.method == "embedded_text":
                    continue
                try:
                    result = recognize(page.image_png, settings.ocr_executable,
                                       settings.ocr_language, settings.ocr_timeout)
                except OCRError as exc:
                    raise HTTPException(503, str(exc)) from exc
                session.add(OCRPageRow(document_id=key, page_number=page.page_number,
                                       **result.model_dump()))
            session.flush()
            return results(session, key)

    @router.get("/{document_id}/ocr", response_model=list[PageOCR])
    def get_ocr(document_id: UUID):
        with sessions() as session:
            if session.get(DocumentRow, str(document_id)) is None:
                raise HTTPException(404, "Document not found")
            return results(session, str(document_id))

    return router
