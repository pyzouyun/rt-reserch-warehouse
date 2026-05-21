"""Database connection helpers."""

from collections.abc import Iterator
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

from etl.config import get_settings

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """Create a SQLAlchemy engine from the configured database URL."""

    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


@contextmanager
def db_connection() -> Iterator[Connection]:
    """Yield a transactional SQLAlchemy connection."""

    engine = get_engine()
    with engine.begin() as connection:
        logger.debug("Opened database transaction")
        yield connection
