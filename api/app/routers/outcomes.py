"""Clinical outcome research-side CRUD endpoints."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.database import execute_returning, fetch_all, fetch_one, scalar_count
from app.schemas import ClinicalOutcomeCreate, ClinicalOutcomeUpdate, collection_response, data_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outcomes", tags=["outcomes"])

OUTCOME_COLUMNS = [
    "id",
    "research_patient_id",
    "outcome_type",
    "outcome_date",
    "outcome_value",
    "grade",
    "metadata",
    "created_at",
    "updated_at",
]
PATCH_FIELDS = {"outcome_type", "outcome_date", "outcome_value", "grade", "metadata"}


@router.get("")
def list_outcomes(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List clinical outcomes."""

    try:
        rows = fetch_all(
            """
            SELECT id, research_patient_id, outcome_type, outcome_date, outcome_value,
                   grade, metadata, created_at, updated_at
            FROM clinical_outcome
            ORDER BY updated_at DESC
            LIMIT :limit OFFSET :offset
            """,
            {"limit": limit, "offset": offset},
        )
        return collection_response(rows, total=scalar_count("clinical_outcome"), limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list outcomes: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)


@router.post("")
def create_outcome(payload: ClinicalOutcomeCreate) -> Dict[str, Any]:
    """Create a clinical outcome."""

    row = execute_returning(
        """
        INSERT INTO clinical_outcome (
            research_patient_id, outcome_type, outcome_date, outcome_value, grade, metadata
        )
        VALUES (
            :research_patient_id, :outcome_type, :outcome_date, :outcome_value, :grade,
            CAST(:metadata AS jsonb)
        )
        RETURNING id, research_patient_id, outcome_type, outcome_date, outcome_value,
                  grade, metadata, created_at, updated_at
        """,
        _payload_params(payload.model_dump()),
    )
    return data_response(row)


@router.get("/{outcome_id}")
def get_outcome(outcome_id: int) -> Dict[str, Any]:
    """Return one clinical outcome."""

    row = fetch_one(
        """
        SELECT id, research_patient_id, outcome_type, outcome_date, outcome_value,
               grade, metadata, created_at, updated_at
        FROM clinical_outcome
        WHERE id = :id
        """,
        {"id": outcome_id},
    )
    return data_response(row)


@router.patch("/{outcome_id}")
def update_outcome(outcome_id: int, payload: ClinicalOutcomeUpdate) -> Dict[str, Any]:
    """Update a clinical outcome."""

    values = payload.model_dump(exclude_unset=True)
    row = _update_allowed("clinical_outcome", outcome_id, values, PATCH_FIELDS, OUTCOME_COLUMNS)
    return data_response(row)


@router.delete("/{outcome_id}")
def delete_outcome(outcome_id: int) -> Dict[str, Any]:
    """Delete a clinical outcome."""

    row = execute_returning(
        """
        DELETE FROM clinical_outcome
        WHERE id = :id
        RETURNING id, research_patient_id, outcome_type, outcome_date, outcome_value,
                  grade, metadata, created_at, updated_at
        """,
        {"id": outcome_id},
    )
    return data_response(row)


def _update_allowed(
    table_name: str,
    row_id: int,
    values: Dict[str, Any],
    allowed_fields: set,
    returning_columns: List[str],
) -> Dict[str, Any]:
    if table_name != "clinical_outcome":
        raise ValueError(f"Unsupported table: {table_name}")
    fields = [field for field in values if field in allowed_fields]
    if not fields:
        raise HTTPException(status_code=400, detail="No supported fields to update")
    params: Dict[str, Any] = {"id": row_id}
    assignments = []
    for field in fields:
        value = values[field]
        if field == "metadata":
            value = json.dumps(value or {})
            assignments.append("metadata = metadata || CAST(:metadata AS jsonb)")
        else:
            assignments.append(f"{field} = :{field}")
        params[field] = value
    columns_sql = ", ".join(returning_columns)
    assignments_sql = ", ".join(assignments)
    row = execute_returning(
        f"""
        UPDATE {table_name}
        SET {assignments_sql}
        WHERE id = :id
        RETURNING {columns_sql}
        """,
        params,
    )
    return row


def _payload_params(values: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(values)
    params["metadata"] = json.dumps(params.get("metadata") or {})
    return params
