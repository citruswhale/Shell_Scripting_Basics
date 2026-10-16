"""CRUD endpoints for equipment items."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import metrics
from app.database import get_db
from app.models import Item, Loan
from app.schemas import Category, ItemCreate, ItemOut, ItemUpdate

router = APIRouter(prefix="/api/items", tags=["items"])


def get_item_or_404(db: Session, item_id: int, lock: bool = False) -> Item:
    stmt = select(Item).where(Item.id == item_id)
    if lock:
        stmt = stmt.with_for_update()
    item = db.scalars(stmt).first()
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Item {item_id} not found")
    return item


def _check_serial_free(db: Session, serial: str | None, own_id: int | None = None) -> None:
    if not serial:
        return
    stmt = select(Item.id).where(Item.serial_number == serial)
    if own_id is not None:
        stmt = stmt.where(Item.id != own_id)
    if db.scalars(stmt).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Serial number '{serial}' is already used")


def _commit(db: Session) -> None:
    """Commit, turning a unique-constraint race into a clean 409."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Serial number is already used")


@router.get("", response_model=list[ItemOut])
def list_items(
    search: str | None = Query(default=None, max_length=100),
    category: Category | None = None,
    status_filter: Literal["available", "on_loan", "maintenance"] | None = Query(
        default=None, alias="status"
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Item)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Item.name.ilike(pattern),
                Item.serial_number.ilike(pattern),
                Item.notes.ilike(pattern),
            )
        )
    if category:
        stmt = stmt.where(Item.category == category)
    if status_filter:
        stmt = stmt.where(Item.status == status_filter)
    stmt = stmt.order_by(Item.name, Item.id).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return get_item_or_404(db, item_id)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    _check_serial_free(db, payload.serial_number)
    item = Item(**payload.model_dump())
    db.add(item)
    _commit(db)
    db.refresh(item)
    metrics.ITEMS_CREATED.inc()
    return item


@router.put("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = get_item_or_404(db, item_id, lock=True)
    changes = payload.model_dump(exclude_unset=True)

    # name and category are required columns, so they can't be cleared
    for field in ("name", "category", "condition"):
        if field in changes and changes[field] is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"{field} cannot be empty")

    new_status = changes.get("status")
    if new_status is not None and new_status != item.status:
        if item.status == "on_loan":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Item is on loan; return the loan to change its status"
            )
        if new_status == "on_loan":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Use the loans endpoint to put an item on loan"
            )
    elif new_status is None:
        changes.pop("status", None)

    if "serial_number" in changes:
        _check_serial_free(db, changes["serial_number"], own_id=item.id)

    for field, value in changes.items():
        setattr(item, field, value)
    _commit(db)
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item_or_404(db, item_id, lock=True)
    active = db.scalars(
        select(Loan.id).where(Loan.item_id == item.id, Loan.status == "active")
    ).first()
    if active is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Item has an active loan and cannot be deleted")
    # Old (returned) loans go with the item so the foreign key doesn't block the delete.
    for loan in list(item.loans):
        db.delete(loan)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
