from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer


class Document(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID | None
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime


    @field_serializer("uploaded_at", when_used="json")
    def serialize_uploaded_at(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class DocumentLink(BaseModel):
    invoice_id: UUID | None
