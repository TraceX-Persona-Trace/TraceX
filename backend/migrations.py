"""
Lightweight runtime migration runner for TraceX.

Each migration function is idempotent — safe to run on every application startup.
Migrations are applied in order. SQLite does not support IF NOT EXISTS on ALTER TABLE,
so each migration checks the current schema before executing.
"""
from sqlalchemy import text
from backend.database import engine


def _column_exists(conn, table: str, column: str) -> bool:
    """Return True if the column already exists on the given table."""
    result = conn.execute(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result.fetchall())


def _migration_add_evidence_normalised_value(conn) -> None:
    """
    Chunk 6: Add normalised_value (nullable VARCHAR) to the evidence table.

    All existing rows receive NULL — they are unaffected by matching logic because
    the matching service explicitly skips attributes where normalised_value IS NULL.
    """
    if not _column_exists(conn, "evidence", "normalised_value"):
        conn.execute(text("ALTER TABLE evidence ADD COLUMN normalised_value VARCHAR"))
        conn.commit()


# Ordered list of all migrations. Append new entries here for future chunks.
_MIGRATIONS = [
    _migration_add_evidence_normalised_value,
]


def run_migrations() -> None:
    """Run all registered migrations in order."""
    with engine.connect() as conn:
        for migration in _MIGRATIONS:
            migration(conn)
