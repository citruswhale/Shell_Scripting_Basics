"""GearLoan API entry point: wires routers, health checks, metrics and CORS."""
import logging

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import engine, get_db
from app.metrics import MetricsMiddleware
from app.models import Item, Loan, today
from app.routers import items, loans
from app.schemas import AppInfo, Stats

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())
log = logging.getLogger("gearloan")

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)

app.include_router(items.router)
app.include_router(loans.router)


# --- health checks -------------------------------------------------------
# /health only says "the process is up" (liveness, never touches the DB).
# /ready also checks the database, so traffic is held back until it works.
# Both are repeated under /api because the ingress sends /api to this service.

@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"], include_in_schema=False)
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
@app.get("/api/ready", tags=["health"], include_in_schema=False)
def ready(response: Response):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # any DB error means "not ready"
        log.warning("readiness check failed: %s", exc)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
@app.get("/api/metrics", include_in_schema=False)
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# --- small info endpoints ------------------------------------------------

@app.get("/api/info", response_model=AppInfo, tags=["info"])
def info():
    return AppInfo(name=settings.app_name, version=settings.app_version)


@app.get("/api/stats", response_model=Stats, tags=["info"])
def stats(db: Session = Depends(get_db)):
    item_row = db.execute(
        select(
            func.count(Item.id),
            func.count(case((Item.status == "available", 1))),
            func.count(case((Item.status == "on_loan", 1))),
            func.count(case((Item.status == "maintenance", 1))),
        )
    ).one()
    loan_row = db.execute(
        select(
            func.count(Loan.id),
            func.count(case((Loan.due_date < today(), 1))),
        ).where(Loan.status == "active")
    ).one()
    # active_loans counts every loan that is still out (overdue ones included);
    # overdue_loans is the part of those that is past its due date.
    return Stats(
        items_total=item_row[0],
        available=item_row[1],
        on_loan=item_row[2],
        maintenance=item_row[3],
        active_loans=loan_row[0],
        overdue_loans=loan_row[1],
    )
