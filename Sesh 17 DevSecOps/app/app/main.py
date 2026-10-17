"""Loan calculator API: works out late fees for overdue equipment."""

import os

from fastapi import FastAPI, Query

from app.fees import GRACE_DAYS, MAX_FEE, late_fee

APP_NAME = "s17-loan-calculator"
APP_VERSION = "1.0.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict:
    # APP_COMMIT is set in the Kubernetes Deployment by the pipeline
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "commit": os.getenv("APP_COMMIT", "local"),
    }


@app.get("/fee")
def fee(
    days_late: int = Query(..., ge=0, le=365, description="Days the item is overdue"),
    daily_rate: float = Query(..., gt=0, le=1000, description="Fee per day in rupees"),
) -> dict:
    # Query() does the validation, bad input gets a 422 from FastAPI
    amount = late_fee(days_late, daily_rate)
    return {
        "days_late": days_late,
        "daily_rate": daily_rate,
        "grace_days": GRACE_DAYS,
        "max_fee": MAX_FEE,
        "fee": amount,
        "capped": amount >= MAX_FEE,
    }
