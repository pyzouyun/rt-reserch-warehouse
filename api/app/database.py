"""Database helpers for dashboard and research-side API queries."""

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """Create a SQLAlchemy engine."""

    return create_engine(get_settings().database_url, pool_pre_ping=True, future=True)


@contextmanager
def get_connection() -> Iterator[Connection]:
    """Yield a database connection."""

    engine = get_engine()
    with engine.connect() as connection:
        yield connection


def scalar_count(table_name: str) -> int:
    """Return a row count for a trusted table name, or zero if unavailable."""

    allowed_tables = {
        "patient_index",
        "dicom_study",
        "dicom_series",
        "dicom_instance",
        "image_archive",
        "rt_structure",
        "rt_plan",
        "rt_dose",
        "dvh_metric",
        "treatment_fraction",
        "mosaiq_prescription",
        "xvi_registration",
        "mosaiq_workflow",
        "clinical_outcome",
        "etl_log",
    }
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table: {table_name}")
    try:
        with get_connection() as connection:
            return int(connection.execute(text(f"SELECT count(*) FROM {table_name}")).scalar_one())
    except Exception as exc:
        logger.warning("Could not count table %s: %s", table_name, exc)
        return 0


def fetch_one(sql: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return one row as a dictionary."""

    with get_connection() as connection:
        row = connection.execute(text(sql), params).mappings().first()
        return dict(row) if row is not None else None


def fetch_all(sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return all rows as dictionaries."""

    with get_connection() as connection:
        rows = connection.execute(text(sql), params).mappings().all()
        return [dict(row) for row in rows]


def execute_returning(sql: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Execute a write query that returns one row and commit it."""

    engine = get_engine()
    with engine.begin() as connection:
        row = connection.execute(text(sql), params).mappings().first()
        return dict(row) if row is not None else None
