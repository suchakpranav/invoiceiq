"""Create invoice table."""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_number", sa.String(150), nullable=False),
        sa.Column("supplier", sa.String(150), nullable=False),
        sa.Column("customer", sa.String(150), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("subtotal_cents", sa.BigInteger(), nullable=False),
        sa.Column("tax_basis_points", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.CheckConstraint("subtotal_cents BETWEEN 0 AND 999999999999"),
        sa.CheckConstraint("tax_basis_points BETWEEN 0 AND 10000"),
    )
    op.create_index("ix_invoices_supplier", "invoices", ["supplier"])
    op.create_index("ix_invoices_invoice_date", "invoices", ["invoice_date"])


def downgrade():
    op.drop_table("invoices")
