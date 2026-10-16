"""Endpoints for lending items out and taking them back."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app import metrics
from app.database import get_db
from app.models import Loan, today
from app.routers.items import get_item_or_404
from app.schemas import LoanCreate, LoanOut, LoanReturn

router = APIRouter(prefix="/api/loans", tags=["loans"])

MAX_ACTIVE_LOANS_PER_BORROWER = 3


def get_loan_or_404(db: Session, loan_id: int, lock: bool = False) -> Loan:
    stmt = select(Loan).where(Loan.id == loan_id)
    if lock:
        stmt = stmt.with_for_update()
    else:
        stmt = stmt.options(joinedload(Loan.item))
    loan = db.scalars(stmt).first()
    if loan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Loan {loan_id} not found")
    return loan


@router.get("", response_model=list[LoanOut])
def list_loans(
    status_filter: Literal["active", "returned", "overdue"] | None = Query(
        default=None, alias="status"
    ),
    borrower_email: str | None = Query(default=None, max_length=254),
    item_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Loan).options(joinedload(Loan.item))
    # The filter matches the status the API shows: "active" means on time,
    # "overdue" means still out and past the due date.
    if status_filter == "returned":
        stmt = stmt.where(Loan.status == "returned")
    elif status_filter == "active":
        stmt = stmt.where(Loan.status == "active", Loan.due_date >= today())
    elif status_filter == "overdue":
        stmt = stmt.where(Loan.status == "active", Loan.due_date < today())
    if borrower_email:
        stmt = stmt.where(func.lower(Loan.borrower_email) == borrower_email.strip().lower())
    if item_id is not None:
        stmt = stmt.where(Loan.item_id == item_id)
    stmt = stmt.order_by(Loan.loaned_at.desc(), Loan.id.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).unique().all()


@router.get("/{loan_id}", response_model=LoanOut)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    return get_loan_or_404(db, loan_id)


@router.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db)):
    # Serialise loans for the same borrower so two quick requests can't both
    # slip under the 3-loan limit. The lock is released at commit/rollback.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:email))"), {"email": payload.borrower_email})

    # Row lock on the item so it can't be lent twice at the same time.
    item = get_item_or_404(db, payload.item_id, lock=True)
    if item.status == "maintenance":
        raise HTTPException(status.HTTP_409_CONFLICT, "Item is in maintenance and cannot be loaned")
    if item.status != "available":
        raise HTTPException(status.HTTP_409_CONFLICT, "Item is already on loan")

    active_count = db.scalar(
        select(func.count(Loan.id)).where(
            func.lower(Loan.borrower_email) == payload.borrower_email,
            Loan.status == "active",
        )
    )
    if active_count >= MAX_ACTIVE_LOANS_PER_BORROWER:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Borrower already has {MAX_ACTIVE_LOANS_PER_BORROWER} active loans",
        )

    loan = Loan(**payload.model_dump(), status="active")
    item.status = "on_loan"
    db.add(loan)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Item is already on loan")
    metrics.LOANS_CREATED.inc()
    return get_loan_or_404(db, loan.id)


@router.api_route("/{loan_id}/return", methods=["POST", "PUT"], response_model=LoanOut)
def return_loan(loan_id: int, payload: LoanReturn | None = None, db: Session = Depends(get_db)):
    loan = get_loan_or_404(db, loan_id, lock=True)
    if loan.status == "returned":
        raise HTTPException(status.HTTP_409_CONFLICT, "Loan has already been returned")

    item = get_item_or_404(db, loan.item_id, lock=True)
    condition = (payload.condition if payload else None) or item.condition

    loan.status = "returned"
    loan.returned_at = datetime.now(timezone.utc)
    loan.return_condition = condition
    item.condition = condition
    item.status = "maintenance" if condition == "damaged" else "available"
    db.commit()
    metrics.LOANS_RETURNED.inc()
    return get_loan_or_404(db, loan.id)


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = get_loan_or_404(db, loan_id, lock=True)
    if loan.status != "returned":
        raise HTTPException(status.HTTP_409_CONFLICT, "Only returned loans can be deleted")
    db.delete(loan)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
