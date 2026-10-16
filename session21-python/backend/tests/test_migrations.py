"""Checks that the Alembic migration and the SQLAlchemy models agree."""
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.database import Base, engine


def test_migration_created_expected_tables(migrated_database):
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"items", "loans", "alembic_version"} <= tables

    index_names = {ix["name"] for ix in inspector.get_indexes("loans")}
    assert "uq_loans_one_active_per_item" in index_names


def test_models_match_migration(migrated_database):
    # If someone changes models.py without writing a migration, this fails.
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []
