"""Import MOSAIQ-like CSV exports into the research database."""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Dict, Optional, Set

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from etl.config import get_settings
from etl.db import db_connection
from etl.deidentify import hash_identifier, research_patient_id
from etl.load_to_db import log_etl_event

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure logging for CSV imports."""

    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def import_csv_directory(csv_dir: Path) -> int:
    """Import available MOSAIQ CSV templates from a directory."""

    settings = get_settings()
    imported = 0
    with db_connection() as connection:
        patient_map = _load_patient_map(csv_dir / "mosaiq_patient.csv", settings.deidentify_salt)
        imported += _import_patients(connection, csv_dir / "mosaiq_patient.csv", settings.deidentify_salt)
        imported += _import_prescriptions(
            connection,
            csv_dir / "mosaiq_prescription.csv",
            patient_map,
            settings.deidentify_salt,
        )

        workflow_path = csv_dir / "mosaiq_workflow.csv"
        if workflow_path.exists():
            workflow = pd.read_csv(workflow_path)
            for _, row in workflow.iterrows():
                patient_key = str(row.get("PatientID", ""))
                research_id = patient_map.get(patient_key) or research_patient_id(patient_key, salt=settings.deidentify_salt)
                connection.execute(
                    text(
                        """
                        INSERT INTO mosaiq_workflow (
                            research_patient_id, workflow_step, workflow_status, scheduled_date,
                            completed_date, source_record_hash, metadata
                        )
                        VALUES (
                            :research_patient_id, :workflow_step, :workflow_status, :scheduled_date,
                            :completed_date, :source_record_hash, CAST(:metadata AS jsonb)
                        )
                        """
                    ),
                    {
                        "research_patient_id": research_id,
                        "workflow_step": row.get("WorkflowStep"),
                        "workflow_status": row.get("Status"),
                        "scheduled_date": _nullable(row.get("ScheduledDate")),
                        "completed_date": _nullable(row.get("CompletedDate")),
                        "source_record_hash": hash_identifier(row.to_json(), salt=settings.deidentify_salt),
                        "metadata": _row_metadata(row, exclude={"PatientID", "CourseID"}),
                    },
                )
                imported += 1

        fraction_path = csv_dir / "mosaiq_fraction.csv"
        if fraction_path.exists():
            fractions = pd.read_csv(fraction_path)
            for _, row in fractions.iterrows():
                patient_key = str(row.get("PatientID", ""))
                research_id = patient_map.get(patient_key) or research_patient_id(patient_key, salt=settings.deidentify_salt)
                connection.execute(
                    text(
                        """
                        INSERT INTO treatment_fraction (
                            research_patient_id, fraction_number, treatment_date, machine_name,
                            delivered_mu, treatment_status, source_record_hash, metadata
                        )
                        VALUES (
                            :research_patient_id, :fraction_number, :treatment_date, :machine_name,
                            :delivered_mu, :treatment_status, :source_record_hash, CAST(:metadata AS jsonb)
                        )
                        """
                    ),
                    {
                        "research_patient_id": research_id,
                        "fraction_number": _nullable(row.get("FractionNumber")),
                        "treatment_date": _nullable(row.get("TreatmentDate")),
                        "machine_name": row.get("MachineName"),
                        "delivered_mu": _nullable(row.get("DeliveredMU")),
                        "treatment_status": row.get("Status"),
                        "source_record_hash": hash_identifier(row.to_json(), salt=settings.deidentify_salt),
                        "metadata": _row_metadata(row, exclude={"PatientID", "CourseID", "PlanID"}),
                    },
                )
                imported += 1

        log_etl_event(
            connection,
            pipeline_name="mosaiq_csv_import",
            status="success",
            message=f"Imported {imported} MOSAIQ CSV rows from {csv_dir}",
            records_processed=imported,
        )
    return imported


def _import_patients(connection: Connection, path: Path, salt: str) -> int:
    if not path.exists():
        return 0
    count = 0
    patients = pd.read_csv(path)
    for _, row in patients.iterrows():
        patient_id = str(row.get("PatientID", ""))
        connection.execute(
            text(
                """
                INSERT INTO patient_index (
                    research_patient_id, patient_id_hash, sex, birth_year, metadata
                )
                VALUES (
                    :research_patient_id, :patient_id_hash, :sex, :birth_year, CAST(:metadata AS jsonb)
                )
                ON CONFLICT (research_patient_id) DO UPDATE SET
                    sex = EXCLUDED.sex,
                    birth_year = EXCLUDED.birth_year,
                    metadata = patient_index.metadata || EXCLUDED.metadata,
                    updated_at = now()
                """
            ),
            {
                "research_patient_id": research_patient_id(patient_id, salt=salt),
                "patient_id_hash": hash_identifier(patient_id, salt=salt),
                "sex": _nullable(row.get("Sex")),
                "birth_year": _nullable(row.get("BirthYear")),
                "metadata": _row_metadata(row, exclude={"PatientID"}),
            },
        )
        count += 1
    return count


def _import_prescriptions(
    connection: Connection,
    path: Path,
    patient_map: Dict[str, str],
    salt: str,
) -> int:
    if not path.exists():
        return 0
    count = 0
    prescriptions = pd.read_csv(path)
    for _, row in prescriptions.iterrows():
        patient_key = str(row.get("PatientID", ""))
        research_id = patient_map.get(patient_key) or research_patient_id(patient_key, salt=salt)
        connection.execute(
            text(
                """
                INSERT INTO mosaiq_prescription (
                    research_patient_id, course_id_hash, plan_id_hash, prescription_dose_gy,
                    fractions, dose_per_fraction_gy, treatment_site, technique,
                    source_record_hash, metadata
                )
                VALUES (
                    :research_patient_id, :course_id_hash, :plan_id_hash, :prescription_dose_gy,
                    :fractions, :dose_per_fraction_gy, :treatment_site, :technique,
                    :source_record_hash, CAST(:metadata AS jsonb)
                )
                """
            ),
            {
                "research_patient_id": research_id,
                "course_id_hash": hash_identifier(row.get("CourseID"), salt=salt),
                "plan_id_hash": hash_identifier(row.get("PlanID"), salt=salt),
                "prescription_dose_gy": _nullable(row.get("PrescriptionDoseGy")),
                "fractions": _nullable(row.get("Fractions")),
                "dose_per_fraction_gy": _nullable(row.get("DosePerFractionGy")),
                "treatment_site": _nullable(row.get("Site")),
                "technique": _nullable(row.get("Technique")),
                "source_record_hash": hash_identifier(row.to_json(), salt=salt),
                "metadata": _row_metadata(row, exclude={"PatientID", "CourseID", "PlanID"}),
            },
        )
        count += 1
    return count


def _load_patient_map(path: Path, salt: str) -> Dict[str, str]:
    if not path.exists():
        logger.warning("Patient CSV not found at %s; deriving ids from row PatientID values", path)
        return {}
    patients = pd.read_csv(path)
    mapping: Dict[str, str] = {}
    for _, row in patients.iterrows():
        patient_id = str(row.get("PatientID", ""))
        mapping[patient_id] = research_patient_id(patient_id, salt=salt)
    return mapping


def _row_metadata(row: pd.Series, *, exclude: Set[str]) -> str:
    """Serialize a CSV row to JSON after removing direct/source identifiers."""

    safe_row = row.drop(labels=[column for column in exclude if column in row.index])
    return safe_row.to_json(force_ascii=False)


def _nullable(value: object) -> Optional[object]:
    if pd.isna(value) or value == "":
        return None
    return value


def main() -> int:
    """CLI entry point."""

    configure_logging()
    settings = get_settings()
    csv_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else settings.mosaiq_csv_dir
    try:
        count = import_csv_directory(csv_dir)
        logger.info("Imported %s MOSAIQ CSV rows", count)
        return 0
    except Exception as exc:
        logger.exception("MOSAIQ CSV import failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
