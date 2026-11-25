from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InvoiceIQ"
    app_version: str = "0.4.0"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://invoiceiq_app:CHANGE_ME@127.0.0.1:5432/invoiceiq"
    log_level: str = "INFO"
    upload_dir: Path = Path("uploads")
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1, le=50 * 1024 * 1024)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="INVOICEIQ_")
