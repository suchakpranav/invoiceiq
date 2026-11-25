from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "InvoiceIQ"
    app_version: str = "0.3.0"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://invoiceiq_app:CHANGE_ME@127.0.0.1:5432/invoiceiq"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="INVOICEIQ_")
