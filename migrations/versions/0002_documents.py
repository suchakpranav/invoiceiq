"""Add document metadata without modifying existing invoices."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_id", sa.String(36),
                  sa.ForeignKey("invoices.id", ondelete="SET NULL")),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(40), nullable=False, unique=True),
        sa.Column("content_type", sa.String(32), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_invoice_id", "documents", ["invoice_id"])
    op.create_index("ix_documents_sha256", "documents", ["sha256"])


def downgrade():
    op.drop_table("documents")
