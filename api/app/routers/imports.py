"""Controlled import action endpoints."""

from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import data_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/imports", tags=["imports"])

EXPECTED_CSV_HEADERS = {
    "mosaiq_patient.csv": {"PatientID", "Sex", "BirthYear"},
    "mosaiq_prescription.csv": {"PatientID", "CourseID", "PlanID", "PrescriptionDoseGy", "Fractions", "DosePerFractionGy"},
    "mosaiq_fraction.csv": {"PatientID", "CourseID", "PlanID", "FractionNumber", "TreatmentDate", "MachineName", "DeliveredMU", "Status"},
    "mosaiq_workflow.csv": {"PatientID", "CourseID", "WorkflowStep", "Status", "ScheduledDate", "CompletedDate"},
}


@router.post("/mosaiq/validate")
def validate_mosaiq_import() -> Dict[str, Any]:
    """Validate MOSAIQ CSV template files and required headers."""

    csv_dir = _mosaiq_csv_dir()
    missing_files: List[str] = []
    header_errors: List[Dict[str, Any]] = []
    for filename, required_headers in EXPECTED_CSV_HEADERS.items():
        path = csv_dir / filename
        if not path.exists():
            missing_files.append(filename)
            continue
        headers = _read_headers(path)
        missing_headers = sorted(required_headers - set(headers))
        if missing_headers:
            header_errors.append({"file": filename, "missing_headers": missing_headers, "headers": headers})
    is_valid = not missing_files and not header_errors
    return data_response(
        {
            "csv_dir": str(csv_dir),
            "ok": is_valid,
            "valid": is_valid,
            "missing_files": missing_files,
            "header_errors": header_errors,
        }
    )


@router.post("/mosaiq/run")
def run_mosaiq_import() -> Dict[str, Any]:
    """Run the existing MOSAIQ CSV import command."""

    return data_response(_run_command([sys.executable, "-m", "etl.import_mosaiq_csv"]))


def _mosaiq_csv_dir() -> Path:
    return Path(os.getenv("MOSAIQ_CSV_DIR", "/app/data_templates"))


def _read_headers(path: Path) -> List[str]:
    try:
        with path.open(newline="") as handle:
            reader = csv.reader(handle)
            return next(reader, [])
    except Exception as exc:
        logger.warning("Could not read CSV header from %s: %s", path, exc)
        return []


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
        logger.exception("MOSAIQ import command failed: %s", exc)
        return {"command": " ".join(command), "exit_code": 1, "stdout": "", "stderr": str(exc)}
