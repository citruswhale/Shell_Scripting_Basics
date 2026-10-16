# GearLoan backend

FastAPI + SQLAlchemy + PostgreSQL API for lending out club equipment.

## Run it locally

You need Python 3.12 and a Postgres database.

```bash
cd backend
uv venv --python 3.12 .venv            # or: python3.12 -m venv .venv
uv pip install --python .venv -r requirements-dev.txt

export DATABASE_URL=postgresql+psycopg://gearloan:gearloan@localhost:5432/gearloan
.venv/bin/alembic upgrade head          # create / update the tables
.venv/bin/uvicorn app.main:app --reload --port 8000
```

API docs are at http://localhost:8000/docs.

## Run the tests

The tests use their own database on port 5433, never the real one.

```bash
cd ..                                            # session21-python/
docker compose -f docker-compose.test.yml up -d --wait
cd backend && .venv/bin/pytest -v
docker compose -f ../docker-compose.test.yml down
```

Use `TEST_DATABASE_URL` to point at a different test database (its name must contain "test").
The suite runs the Alembic migration from scratch, so it also checks the migration.

## Settings (environment variables)

| Variable       | Default                                        | What it does                         |
|----------------|------------------------------------------------|--------------------------------------|
| `DATABASE_URL` | `postgresql+psycopg://gearloan:gearloan@localhost:5432/gearloan` | Database connection |
| `APP_VERSION`  | `1.0.0`                                        | Shown by `GET /api/info`             |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173`  | Comma separated allowed origins      |
| `LOG_LEVEL`    | `info`                                         | Python log level                     |

## Endpoints

- `GET /health`, `GET /ready` (also under `/api/...`): liveness (no DB) and readiness (runs `SELECT 1`, 503 if the DB is down)
- `GET /metrics` (also `/api/metrics`): Prometheus metrics
- `GET /api/info`, `GET /api/stats`
- Items: `GET/POST /api/items`, `GET/PUT/DELETE /api/items/{id}`; filters `?search=&category=&status=`
- Loans: `GET/POST /api/loans`, `GET/DELETE /api/loans/{id}`, `POST /api/loans/{id}/return`; filters `?status=active|overdue|returned&borrower_email=`

A few rules worth knowing:

- Only `available` items can be lent; lending sets the item to `on_loan`.
- Returning with condition `damaged` puts the item in `maintenance`, otherwise it goes back to `available`.
- One borrower (by email, case-insensitive) can have at most 3 loans out at once.
- Loan status `overdue` is not stored; it is worked out from `due_date` each time.
  The `status=active` filter returns on-time loans only. In `/api/stats`, `active_loans`
  counts every loan still out and `overdue_loans` is the late part of those.

## Docker

```bash
docker build -t gearloan-backend .
```

The container runs as user 10001. On start, `entrypoint.sh` runs `alembic upgrade head`
(protected by a Postgres advisory lock so several replicas don't migrate at once) and then
starts uvicorn on port 8000.
