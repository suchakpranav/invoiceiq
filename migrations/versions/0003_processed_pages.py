"""Store extracted text and bounded OCR-ready page images."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "processed_pages",
        sa.Column("document_id", sa.String(36),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("page_number", sa.Integer(), primary_key=True),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("image_png", sa.LargeBinary(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.CheckConstraint("page_number >= 1"),
    )


def downgrade():
    op.drop_table("processed_pages")
