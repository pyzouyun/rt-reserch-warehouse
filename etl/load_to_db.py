"""Load parsed DICOM and CSV-derived records into PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict

from sqlalchemy import text
from sqlalchemy.engine import Connection

from etl.parse_dicom import ParsedDicom

logger = logging.getLogger(__name__)


def upsert_parsed_dicom(connection: Connection, parsed: ParsedDicom) -> None:
    """Upsert the patient, study, series, instance, and RT-specific records."""

    patient_pk = _upsert_patient(connection, parsed)
    study_pk = _upsert_study(connection, parsed, patient_pk)
    series_pk = _upsert_series(connection, parsed, study_pk)
    instance_pk = _upsert_instance(connection, parsed, series_pk)

    if parsed.rt_structure:
        _upsert_json_record(connection, "rt_structure", "dicom_instance_id", instance_pk, parsed.rt_structure)
    if parsed.rt_plan:
        _upsert_json_record(connection, "rt_plan", "dicom_instance_id", instance_pk, parsed.rt_plan)
    if parsed.rt_dose:
        _upsert_json_record(connection, "rt_dose", "dicom_instance_id", instance_pk, parsed.rt_dose)
    if parsed.xvi_registration:
        _upsert_json_record(connection, "xvi_registration", "dicom_instance_id", instance_pk, parsed.xvi_registration)
    if parsed.image_archive:
        _upsert_image_archive(connection, parsed, series_pk)


def promote_contextual_planning_ct(connection: Connection) -> int:
    """Promote CT archive rows to planning CT when their study has RT context."""

    result = connection.execute(
        text(
            """
            UPDATE image_archive ia
            SET
                image_role = 'planning_ct',
                source_system = CASE
                    WHEN ia.source_system = 'Unknown' THEN 'Monaco'
                    ELSE ia.source_system
                END,
                metadata = ia.metadata || '{"classification_reason": "rt_context"}'::jsonb,
                updated_at = now()
            FROM dicom_series ct_series
            WHERE ia.dicom_series_id = ct_series.id
              AND ia.image_role = 'unknown_ct'
              AND EXISTS (
                  SELECT 1
                  FROM dicom_series rt_series
                  JOIN dicom_instance rt_instance ON rt_instance.dicom_series_id = rt_series.id
                  LEFT JOIN rt_plan rp ON rp.dicom_instance_id = rt_instance.id
                  LEFT JOIN rt_structure rs ON rs.dicom_instance_id = rt_instance.id
                  LEFT JOIN rt_dose rd ON rd.dicom_instance_id = rt_instance.id
                  WHERE rt_series.dicom_study_id = ct_series.dicom_study_id
                    AND (rp.id IS NOT NULL OR rs.id IS NOT NULL OR rd.id IS NOT NULL)
              )
            """
        )
    )
    return int(result.rowcount or 0)


def log_etl_event(
    connection: Connection,
    *,
    pipeline_name: str,
    status: str,
    message: str,
    records_processed: int = 0,
) -> None:
    """Write one ETL log entry."""

    connection.execute(
        text(
            """
            INSERT INTO etl_log (pipeline_name, status, message, records_processed, started_at, finished_at)
            VALUES (:pipeline_name, :status, :message, :records_processed, :started_at, :finished_at)
            """
        ),
        {
            "pipeline_name": pipeline_name,
            "status": status,
            "message": message,
            "records_processed": records_processed,
            "started_at": datetime.now(timezone.utc),
            "finished_at": datetime.now(timezone.utc),
        },
    )


def _upsert_patient(connection: Connection, parsed: ParsedDicom) -> int:
    row = connection.execute(
        text(
            """
            INSERT INTO patient_index (research_patient_id, patient_id_hash, patient_name_present)
            VALUES (:research_patient_id, :patient_id_hash, :patient_name_present)
            ON CONFLICT (research_patient_id) DO UPDATE SET
                patient_id_hash = EXCLUDED.patient_id_hash,
                patient_name_present = EXCLUDED.patient_name_present,
                updated_at = now()
            RETURNING id
            """
        ),
        parsed.patient.__dict__,
    ).one()
    return int(row.id)


def _upsert_study(connection: Connection, parsed: ParsedDicom, patient_pk: int) -> int:
    row = connection.execute(
        text(
            """
            INSERT INTO dicom_study (
                patient_index_id, study_instance_uid_hash, accession_number_hash, study_date, study_description
            )
            VALUES (:patient_index_id, :study_instance_uid_hash, :accession_number_hash, :study_date, :study_description)
            ON CONFLICT (study_instance_uid_hash) DO UPDATE SET
                patient_index_id = EXCLUDED.patient_index_id,
                accession_number_hash = EXCLUDED.accession_number_hash,
                study_date = EXCLUDED.study_date,
                study_description = EXCLUDED.study_description,
                updated_at = now()
            RETURNING id
            """
        ),
        {"patient_index_id": patient_pk, **parsed.study.__dict__},
    ).one()
    return int(row.id)


def _upsert_series(connection: Connection, parsed: ParsedDicom, study_pk: int) -> int:
    row = connection.execute(
        text(
            """
            INSERT INTO dicom_series (
                dicom_study_id, series_instance_uid_hash, modality, series_number,
                series_description, frame_of_reference_uid_hash
            )
            VALUES (
                :dicom_study_id, :series_instance_uid_hash, :modality, :series_number,
                :series_description, :frame_of_reference_uid_hash
            )
            ON CONFLICT (series_instance_uid_hash) DO UPDATE SET
                dicom_study_id = EXCLUDED.dicom_study_id,
                modality = EXCLUDED.modality,
                series_number = EXCLUDED.series_number,
                series_description = EXCLUDED.series_description,
                frame_of_reference_uid_hash = EXCLUDED.frame_of_reference_uid_hash,
                updated_at = now()
            RETURNING id
            """
        ),
        {"dicom_study_id": study_pk, **parsed.series.__dict__},
    ).one()
    return int(row.id)


def _upsert_instance(connection: Connection, parsed: ParsedDicom, series_pk: int) -> int:
    row = connection.execute(
        text(
            """
            INSERT INTO dicom_instance (
                dicom_series_id, sop_instance_uid_hash, sop_class_uid, modality,
                instance_number, orthanc_instance_id
            )
            VALUES (
                :dicom_series_id, :sop_instance_uid_hash, :sop_class_uid, :modality,
                :instance_number, :orthanc_instance_id
            )
            ON CONFLICT (sop_instance_uid_hash) DO UPDATE SET
                dicom_series_id = EXCLUDED.dicom_series_id,
                sop_class_uid = EXCLUDED.sop_class_uid,
                modality = EXCLUDED.modality,
                instance_number = EXCLUDED.instance_number,
                orthanc_instance_id = EXCLUDED.orthanc_instance_id,
                updated_at = now()
            RETURNING id
            """
        ),
        {"dicom_series_id": series_pk, **parsed.instance.__dict__},
    ).one()
    return int(row.id)


def _upsert_json_record(connection: Connection, table: str, key_column: str, key_id: int, payload: Dict[str, Any]) -> None:
    allowed = {"rt_structure", "rt_plan", "rt_dose", "xvi_registration"}
    if table not in allowed:
        raise ValueError(f"Unsupported table: {table}")
    connection.execute(
        text(
            f"""
            INSERT INTO {table} ({key_column}, metadata)
            VALUES (:key_id, CAST(:metadata AS jsonb))
            ON CONFLICT ({key_column}) DO UPDATE SET
                metadata = EXCLUDED.metadata,
                updated_at = now()
            """
        ),
        {"key_id": key_id, "metadata": json.dumps(payload, ensure_ascii=False)},
    )


def _upsert_image_archive(connection: Connection, parsed: ParsedDicom, series_pk: int) -> None:
    if parsed.image_archive is None:
        return
    payload = parsed.image_archive.__dict__.copy()
    payload["dicom_series_id"] = series_pk
    payload["metadata"] = json.dumps(payload["metadata"], ensure_ascii=False)
    connection.execute(
        text(
            """
            INSERT INTO image_archive (
                research_patient_id, dicom_series_id, image_role, source_system,
                acquisition_date, acquisition_time, series_instance_uid_hash,
                frame_of_reference_uid_hash, study_description, series_description,
                orthanc_instance_id, metadata
            )
            VALUES (
                :research_patient_id, :dicom_series_id, :image_role, :source_system,
                :acquisition_date, :acquisition_time, :series_instance_uid_hash,
                :frame_of_reference_uid_hash, :study_description, :series_description,
                :orthanc_instance_id, CAST(:metadata AS jsonb)
            )
            ON CONFLICT (dicom_series_id) DO UPDATE SET
                research_patient_id = EXCLUDED.research_patient_id,
                image_role = EXCLUDED.image_role,
                source_system = EXCLUDED.source_system,
                acquisition_date = EXCLUDED.acquisition_date,
                acquisition_time = EXCLUDED.acquisition_time,
                series_instance_uid_hash = EXCLUDED.series_instance_uid_hash,
                frame_of_reference_uid_hash = EXCLUDED.frame_of_reference_uid_hash,
                study_description = EXCLUDED.study_description,
                series_description = EXCLUDED.series_description,
                orthanc_instance_id = EXCLUDED.orthanc_instance_id,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            """
        ),
        payload,
    )
