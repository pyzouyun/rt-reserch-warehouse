"""Patient research index endpoints."""

from __future__ import annotations

import logging
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database import execute_returning, get_connection
from app.schemas import PatientResearchStateUpdate, collection_response, data_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients(
    q: Optional[str] = Query(default=None, max_length=128),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List pseudonymous patient records."""

    where = "WHERE research_patient_id ILIKE :query" if q else ""
    params = {"limit": limit, "offset": offset, "query": f"%{q}%"}
    try:
        with get_connection() as connection:
            total = int(
                connection.execute(text(f"SELECT count(*) FROM patient_index {where}"), params).scalar_one()
            )
            rows = connection.execute(
                text(
                    f"""
                    SELECT research_patient_id, patient_id_hash, sex, birth_year, created_at, updated_at
                    FROM patient_index
                    {where}
                    ORDER BY updated_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            )
            return collection_response([dict(row._mapping) for row in rows], total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list patients: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)


@router.get("/{research_patient_id}")
def patient_detail(research_patient_id: str) -> Dict[str, Any]:
    """Return one patient with related research records."""

    try:
        with get_connection() as connection:
            patient = connection.execute(
                text(
                    """
                    SELECT research_patient_id, patient_id_hash, sex, birth_year, metadata, created_at, updated_at
                    FROM patient_index
                    WHERE research_patient_id = :research_patient_id
                    """
                ),
                {"research_patient_id": research_patient_id},
            ).mappings().first()
            if patient is None:
                return data_response(None)
            return data_response(
                {
                    "patient": dict(patient),
                    "studies": _rows(
                        connection,
                        """
                        SELECT ds.study_instance_uid_hash, ds.study_date, ds.study_description
                        FROM dicom_study ds
                        JOIN patient_index pi ON pi.id = ds.patient_index_id
                        WHERE pi.research_patient_id = :research_patient_id
                        ORDER BY ds.study_date DESC NULLS LAST
                        """,
                        research_patient_id,
                    ),
                    "fractions": _rows(
                        connection,
                        """
                        SELECT fraction_number, treatment_date, machine_name, treatment_status
                        FROM treatment_fraction
                        WHERE research_patient_id = :research_patient_id
                        ORDER BY treatment_date DESC NULLS LAST, fraction_number DESC NULLS LAST
                        LIMIT 50
                        """,
                        research_patient_id,
                    ),
                    "workflows": _rows(
                        connection,
                        """
                        SELECT workflow_step, workflow_status, scheduled_date, completed_date
                        FROM mosaiq_workflow
                        WHERE research_patient_id = :research_patient_id
                        ORDER BY scheduled_date DESC NULLS LAST
                        LIMIT 50
                        """,
                        research_patient_id,
                    ),
                }
            )
    except Exception as exc:
        logger.warning("Could not load patient %s: %s", research_patient_id, exc)
        return data_response(None)


@router.patch("/{research_patient_id}/research-state")
def update_research_state(research_patient_id: str, payload: PatientResearchStateUpdate) -> Dict[str, Any]:
    """Merge research queue state into patient metadata."""

    research_state = payload.model_dump(exclude_unset=True)
    row = execute_returning(
        """
        UPDATE patient_index
        SET metadata = metadata || CAST(:metadata_patch AS jsonb)
        WHERE research_patient_id = :research_patient_id
        RETURNING research_patient_id, patient_id_hash, sex, birth_year, metadata, created_at, updated_at
        """,
        {
            "research_patient_id": research_patient_id,
            "research_state": research_state,
            "metadata_patch": json.dumps({"research_state": research_state}),
        },
    )
    return data_response(row)


def _rows(connection: Any, sql: str, research_patient_id: str) -> List[Dict[str, Any]]:
    rows = connection.execute(text(sql), {"research_patient_id": research_patient_id})
    return [dict(row._mapping) for row in rows]
