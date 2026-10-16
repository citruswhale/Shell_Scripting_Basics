"""Shared pytest fixtures.

The tests always run against a separate Postgres database (TEST_DATABASE_URL),
never the real one. The schema is built with Alembic so the migration itself
gets tested on every run.
"""
import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://gearloan:gearloan@localhost:5433/gearloan_test",
)

# Refuse to run against anything that doesn't look like a test database.
if "test" not in (make_url(TEST_DATABASE_URL).database or ""):
    raise RuntimeError(f"TEST_DATABASE_URL must point to a *test* database, got {TEST_DATABASE_URL}")

# Must happen before the app is imported, because app.database builds its engine on import.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["database_url"] = TEST_DATABASE_URL
    cfg.attributes["configure_logger"] = False
    return cfg


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Start from an empty schema, run every migration, and drop it all at the end."""
    check = create_engine(TEST_DATABASE_URL)
    try:
        with check.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.exit(
            f"Test database not reachable at {TEST_DATABASE_URL}. "
            "Start it with: docker compose -f docker-compose.test.yml up -d\n"
            f"({exc})",
            returncode=2,
        )
    finally:
        check.dispose()

    cfg = _alembic_config()
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield
    engine.dispose()
    command.downgrade(cfg, "base")


@pytest.fixture(autouse=True)
def clean_tables():
    """Every test starts with empty tables."""
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE loans, items RESTART IDENTITY CASCADE"))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --- small helpers used by many tests --------------------------------------

def in_days(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


@pytest.fixture
def make_item(client):
    def _make(name="Canon EOS R50", category="camera", **extra):
        resp = client.post("/api/items", json={"name": name, "category": category, **extra})
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def make_loan(client):
    def _make(item_id, email="asha@college.edu", name="Asha Rao", days=7):
        resp = client.post(
            "/api/loans",
            json={
                "item_id": item_id,
                "borrower_name": name,
                "borrower_email": email,
                "due_date": in_days(days),
            },
        )
        return resp

    return _make
