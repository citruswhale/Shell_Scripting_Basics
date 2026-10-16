"""Pydantic models for request validation and response shapes."""
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import today

Category = Literal["camera", "laptop", "audio", "lighting", "tripod", "other"]
Condition = Literal["good", "fair", "damaged"]
ItemStatus = Literal["available", "on_loan", "maintenance"]
LoanStatus = Literal["active", "returned", "overdue"]

MAX_LOAN_DAYS = 30


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class ItemBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    category: Category
    serial_number: str | None = Field(default=None, max_length=64)
    condition: Condition = "good"
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("serial_number", "notes", mode="before")
    @classmethod
    def empty_string_is_none(cls, v):
        return _blank_to_none(v) if isinstance(v, str) else v


class ItemCreate(ItemBase):
    # New items start as available, or straight in maintenance. "on_loan" only comes from a loan.
    status: Literal["available", "maintenance"] = "available"


class ItemUpdate(BaseModel):
    """All fields optional, only the ones sent are changed."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=100)
    category: Category | None = None
    serial_number: str | None = Field(default=None, max_length=64)
    condition: Condition | None = None
    status: ItemStatus | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("serial_number", "notes", mode="before")
    @classmethod
    def empty_string_is_none(cls, v):
        return _blank_to_none(v) if isinstance(v, str) else v


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: Category
    serial_number: str | None
    condition: Condition
    status: ItemStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LoanCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    item_id: int = Field(gt=0)
    borrower_name: str = Field(min_length=2, max_length=100)
    borrower_email: EmailStr
    due_date: date

    @field_validator("borrower_email")
    @classmethod
    def lower_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("due_date")
    @classmethod
    def due_date_in_range(cls, v: date) -> date:
        now = today()
        if v < now:
            raise ValueError("due_date cannot be in the past")
        if v > now + timedelta(days=MAX_LOAN_DAYS):
            raise ValueError(f"due_date can be at most {MAX_LOAN_DAYS} days from today")
        return v


class LoanReturn(BaseModel):
    # If not given, the item keeps the condition it had before the loan.
    condition: Condition | None = None


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    item_name: str | None = None
    borrower_name: str
    borrower_email: str
    loaned_at: datetime
    due_date: date
    returned_at: datetime | None
    return_condition: Condition | None
    # Read from Loan.current_status so overdue is always up to date.
    status: LoanStatus = Field(validation_alias="current_status")


class Stats(BaseModel):
    items_total: int
    available: int
    on_loan: int
    maintenance: int
    active_loans: int
    overdue_loans: int


class AppInfo(BaseModel):
    name: str
    version: str
