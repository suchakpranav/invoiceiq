"""Persist OCR results tied to prepared pages."""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ocr_pages",
        sa.Column("document_id", sa.String(36), primary_key=True),
        sa.Column("page_number", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("words", sa.JSON(), nullable=False),
        sa.Column("mean_confidence", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id", "page_number"],
            ["processed_pages.document_id", "processed_pages.page_number"],
            ondelete="CASCADE",
        ),
    )


def downgrade():
    op.drop_table("ocr_pages")
