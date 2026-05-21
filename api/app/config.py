"""API configuration."""

from functools import lru_cache
import os
from typing import List
from pathlib import Path

from pydantic import BaseModel
from dotenv import load_dotenv


class ApiSettings(BaseModel):
    """Runtime settings for the API service."""

    database_url: str
    cors_origins: List[str]
    etl_workdir: str


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    """Load API settings from environment variables."""

    legacy_home = os.getenv("RT_RESEARCH_HOME")
    if legacy_home:
        load_dotenv(Path(legacy_home) / "config" / ".env")
    load_dotenv()
    postgres_user = os.getenv("POSTGRES_USER", "rt_research")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db = os.getenv("POSTGRES_DB", "rt_research")
    database_url = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg2://{postgres_user}:{postgres_password}@postgres:5432/{postgres_db}",
    )
    origins = os.getenv("API_CORS_ORIGINS", "http://localhost:5173,http://localhost:8080")
    return ApiSettings(
        database_url=database_url,
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        etl_workdir=os.getenv("ETL_WORKDIR", "/app"),
    )
