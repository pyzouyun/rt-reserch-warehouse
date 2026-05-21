"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime settings for Orthanc, PostgreSQL, and de-identification."""

    orthanc_url: str
    orthanc_username: str
    orthanc_password: str
    database_url: str
    deidentify_salt: str
    log_level: str
    mosaiq_csv_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once from `.env` and process environment variables."""

    legacy_home = os.getenv("RT_RESEARCH_HOME")
    if legacy_home:
        load_dotenv(Path(legacy_home) / "config" / ".env")
    load_dotenv()
    postgres_user = os.getenv("POSTGRES_USER", "rt_research")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_db = os.getenv("POSTGRES_DB", "rt_research")
    return Settings(
        orthanc_url=os.getenv("ORTHANC_URL", "http://orthanc:8042").rstrip("/"),
        orthanc_username=os.getenv("ORTHANC_USERNAME", "orthanc"),
        orthanc_password=os.getenv("ORTHANC_PASSWORD", ""),
        database_url=os.getenv(
            "DATABASE_URL",
            f"postgresql+psycopg2://{postgres_user}:{postgres_password}@postgres:5432/{postgres_db}",
        ),
        deidentify_salt=os.getenv("DEIDENTIFY_SALT", "change-me-in-production"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        mosaiq_csv_dir=Path(os.getenv("MOSAIQ_CSV_DIR", "/app/data_templates")),
    )
