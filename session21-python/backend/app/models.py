"""SQLAlchemy models for items and loans."""
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

CATEGORIES = ("camera", "laptop", "audio", "lighting", "tripod", "other")
CONDITIONS = ("good", "fair", "damaged")
ITEM_STATUSES = ("available", "on_loan", "maintenance")
# Only these two are stored. "overdue" is worked out from due_date when reading.
LOAN_STORED_STATUSES = ("active", "returned")


def _in_list(column: str, values: tuple[str, ...]) -> str:
    quoted = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({quoted})"


def today() -> date:
    """Kept in one place so the whole app agrees on what 'today' is."""
    return date.today()


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        UniqueConstraint("serial_number", name="uq_items_serial_number"),
        CheckConstraint(_in_list("category", CATEGORIES), name="ck_items_category"),
        CheckConstraint(_in_list("condition", CONDITIONS), name="ck_items_condition"),
        CheckConstraint(_in_list("status", ITEM_STATUSES), name="ck_items_status"),
        CheckConstraint("char_length(name) BETWEEN 2 AND 100", name="ck_items_name_length"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    serial_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    condition: Mapped[str] = mapped_column(String(20), nullable=False, server_default="good")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="available", index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    loans: Mapped[list["Loan"]] = relationship(back_populates="item")


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint(_in_list("status", LOAN_STORED_STATUSES), name="ck_loans_status"),
        CheckConstraint(
            "return_condition IS NULL OR " + _in_list("return_condition", CONDITIONS),
            name="ck_loans_return_condition",
        ),
        # A returned loan must have a return time, an active one must not.
        CheckConstraint(
            "(status = 'returned') = (returned_at IS NOT NULL)", name="ck_loans_returned_at"
        ),
        # Safety net at the database level: one active loan per item.
        Index(
            "uq_loans_one_active_per_item",
            "item_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_loans_borrower_email", "borrower_email"),
        Index("ix_loans_status_due_date", "status", "due_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT", name="fk_loans_item_id_items"),
        nullable=False,
        index=True,
    )
    borrower_name: Mapped[str] = mapped_column(String(100), nullable=False)
    borrower_email: Mapped[str] = mapped_column(String(254), nullable=False)
    loaned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    return_condition: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")

    item: Mapped[Item] = relationship(back_populates="loans")

    @property
    def current_status(self) -> str:
        """active / returned / overdue, as shown to API clients."""
        if self.status == "active" and self.due_date < today():
            return "overdue"
        return self.status

    @property
    def item_name(self) -> str | None:
        return self.item.name if self.item else None
