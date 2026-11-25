import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.api.documents import document_router
from app.api.invoices import invoice_router
from app.api.ocr import ocr_router
from app.api.processing import processing_router
from app.core.config import Settings
from app.db.session import build_engine
from app.repositories.invoice import InvoiceRepository

STATIC_DIR = Path(__file__).resolve().parent / "static"
logger = logging.getLogger(__name__)


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level.upper())
    engine = build_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(api: FastAPI):
        try:
            yield
        finally:
            engine.dispose()

    api = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    api.include_router(invoice_router(InvoiceRepository(engine)))
    api.include_router(document_router(engine, settings.upload_dir, settings.max_upload_bytes))
    api.include_router(processing_router(engine, settings.upload_dir))
    api.include_router(ocr_router(engine, settings))
    api.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @api.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @api.get("/api/v1/health", response_model=HealthStatus)
    def health() -> HealthStatus:
        logger.debug("Health endpoint requested")
        return HealthStatus(
            status="ok", version=settings.app_version, environment=settings.environment
        )

    return api


app = create_app()
