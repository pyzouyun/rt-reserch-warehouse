"""ETL monitoring and trigger endpoints."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Any, Dict, List

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.config import get_settings
from app.database import get_connection
from app.schemas import collection_response, data_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/etl", tags=["etl"])


@router.get("/logs")
def logs(limit: int = Query(default=25, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    """List ETL log rows."""

    try:
        with get_connection() as connection:
            total = int(connection.execute(text("SELECT count(*) FROM etl_log")).scalar_one())
            rows = connection.execute(
                text(
                    """
                    SELECT pipeline_name, status, message, records_processed, started_at, finished_at, created_at
                    FROM etl_log
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": limit, "offset": offset},
            )
            return collection_response([dict(row._mapping) for row in rows], total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list ETL logs: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)


@router.post("/run-orthanc")
def run_orthanc_etl() -> Dict[str, Any]:
    """Trigger the Orthanc DICOM ETL as a controlled subprocess."""

    return data_response(_run_command([sys.executable, "-m", "etl.run_etl"]))


@router.post("/import-mosaiq")
def import_mosaiq() -> Dict[str, Any]:
    """Trigger MOSAIQ CSV import as a controlled subprocess."""

    return data_response(_run_command([sys.executable, "-m", "etl.import_mosaiq_csv"]))


def _run_command(command: List[str]) -> Dict[str, Any]:
    settings = get_settings()
    try:
        result = subprocess.run(
            command,
            cwd=settings.etl_workdir,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        return {
            "command": " ".join(command),
            "exit_code": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }
    except Exception as exc:
        logger.exception("ETL command failed: %s", exc)
        return {"command": " ".join(command), "exit_code": 1, "stdout": "", "stderr": str(exc)}
