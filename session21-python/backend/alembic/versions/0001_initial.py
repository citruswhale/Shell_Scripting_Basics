"""Create items and loans tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("serial_number", sa.String(64), nullable=True),
        sa.Column("condition", sa.String(20), nullable=False, server_default="good"),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("serial_number", name="uq_items_serial_number"),
        sa.CheckConstraint(
            "category IN ('camera', 'laptop', 'audio', 'lighting', 'tripod', 'other')",
            name="ck_items_category",
        ),
        sa.CheckConstraint("condition IN ('good', 'fair', 'damaged')", name="ck_items_condition"),
        sa.CheckConstraint(
            "status IN ('available', 'on_loan', 'maintenance')", name="ck_items_status"
        ),
        sa.CheckConstraint("char_length(name) BETWEEN 2 AND 100", name="ck_items_name_length"),
    )
    op.create_index("ix_items_category", "items", ["category"])
    op.create_index("ix_items_status", "items", ["status"])

    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("items.id", ondelete="RESTRICT", name="fk_loans_item_id_items"),
            nullable=False,
        ),
        sa.Column("borrower_name", sa.String(100), nullable=False),
        sa.Column("borrower_email", sa.String(254), nullable=False),
        sa.Column("loaned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_condition", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.CheckConstraint("status IN ('active', 'returned')", name="ck_loans_status"),
        sa.CheckConstraint(
            "return_condition IS NULL OR return_condition IN ('good', 'fair', 'damaged')",
            name="ck_loans_return_condition",
        ),
        sa.CheckConstraint(
            "(status = 'returned') = (returned_at IS NOT NULL)", name="ck_loans_returned_at"
        ),
    )
    op.create_index("ix_loans_item_id", "loans", ["item_id"])
    op.create_index("ix_loans_borrower_email", "loans", ["borrower_email"])
    op.create_index("ix_loans_status_due_date", "loans", ["status", "due_date"])
    # Only one active loan per item, enforced by Postgres itself.
    op.create_index(
        "uq_loans_one_active_per_item",
        "loans",
        ["item_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_table("loans")
    op.drop_table("items")
