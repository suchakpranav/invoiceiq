from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class InvoiceRow(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("subtotal_cents BETWEEN 0 AND 999999999999"),
        CheckConstraint("tax_basis_points BETWEEN 0 AND 10000"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(150))
    supplier: Mapped[str] = mapped_column(String(150), index=True)
    customer: Mapped[str] = mapped_column(String(150))
    invoice_date: Mapped[date] = mapped_column(Date, index=True)
    subtotal_cents: Mapped[int] = mapped_column(BigInteger)
    tax_basis_points: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(500))


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    invoice_id: Mapped[str | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(40), unique=True)
    content_type: Mapped[str] = mapped_column(String(32))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ProcessedPageRow(Base):
    __tablename__ = "processed_pages"
    __table_args__ = (CheckConstraint("page_number >= 1"),)

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    page_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    method: Mapped[str] = mapped_column(String(20))
    extracted_text: Mapped[str] = mapped_column(Text)
    image_png: Mapped[bytes | None]
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)


class OCRPageRow(Base):
    __tablename__ = "ocr_pages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "page_number"],
            ["processed_pages.document_id", "processed_pages.page_number"],
            ondelete="CASCADE",
        ),
    )
    document_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    page_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    words: Mapped[list] = mapped_column(JSON)
    mean_confidence: Mapped[float | None] = mapped_column(Float)
