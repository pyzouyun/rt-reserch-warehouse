"""MOSAIQ-derived data endpoints."""

from __future__ import annotations

import logging
import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.database import execute_returning, get_connection
from app.schemas import (
    TreatmentFractionCreate,
    TreatmentFractionUpdate,
    WorkflowCreate,
    WorkflowUpdate,
    collection_response,
    data_response,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mosaiq", tags=["mosaiq"])

FRACTION_COLUMNS = [
    "id",
    "research_patient_id",
    "fraction_number",
    "treatment_date",
    "machine_name",
    "delivered_mu",
    "treatment_status",
    "metadata",
    "created_at",
    "updated_at",
]
WORKFLOW_COLUMNS = [
    "id",
    "research_patient_id",
    "workflow_step",
    "workflow_status",
    "scheduled_date",
    "completed_date",
    "metadata",
    "created_at",
    "updated_at",
]
FRACTION_PATCH_FIELDS = {"fraction_number", "treatment_date", "machine_name", "delivered_mu", "treatment_status", "metadata"}
WORKFLOW_PATCH_FIELDS = {"workflow_step", "workflow_status", "scheduled_date", "completed_date", "metadata"}
UI_METADATA = {"source": "ui", "editable": True}


@router.get("/prescriptions")
def prescriptions(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    """List MOSAIQ prescription imports."""

    return _list_table(
        """
        SELECT research_patient_id, prescription_dose_gy, fractions, dose_per_fraction_gy,
               treatment_site, technique, updated_at
        FROM mosaiq_prescription
        ORDER BY updated_at DESC
        LIMIT :limit OFFSET :offset
        """,
        "mosaiq_prescription",
        limit,
        offset,
    )


@router.get("/fractions")
def fractions(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    """List treatment fractions."""

    return _list_table(
        """
        SELECT id, research_patient_id, fraction_number, treatment_date, machine_name,
               delivered_mu, treatment_status, metadata, updated_at
        FROM treatment_fraction
        ORDER BY treatment_date DESC NULLS LAST, updated_at DESC
        LIMIT :limit OFFSET :offset
        """,
        "treatment_fraction",
        limit,
        offset,
    )


@router.post("/fractions")
def create_fraction(payload: TreatmentFractionCreate) -> Dict[str, Any]:
    """Create a research-side treatment fraction row."""

    values = payload.model_dump()
    values["metadata"] = _ui_metadata(values.get("metadata"))
    row = execute_returning(
        """
        INSERT INTO treatment_fraction (
            research_patient_id, fraction_number, treatment_date, machine_name,
            delivered_mu, treatment_status, metadata
        )
        VALUES (
            :research_patient_id, :fraction_number, :treatment_date, :machine_name,
            :delivered_mu, :treatment_status, CAST(:metadata AS jsonb)
        )
        RETURNING id, research_patient_id, fraction_number, treatment_date, machine_name,
                  delivered_mu, treatment_status, metadata, created_at, updated_at
        """,
        _json_params(values),
    )
    return data_response(_normalize_metadata(row))


@router.patch("/fractions/{fraction_id}")
def update_fraction(fraction_id: int, payload: TreatmentFractionUpdate) -> Dict[str, Any]:
    """Update a treatment fraction row."""

    row = _update_allowed(
        "treatment_fraction",
        fraction_id,
        payload.model_dump(exclude_unset=True),
        FRACTION_PATCH_FIELDS,
        FRACTION_COLUMNS,
    )
    return data_response(_normalize_metadata(row))


@router.delete("/fractions/{fraction_id}")
def delete_fraction(fraction_id: int) -> Dict[str, Any]:
    """Delete a treatment fraction row."""

    row = execute_returning(
        """
        DELETE FROM treatment_fraction
        WHERE id = :id
        RETURNING id, research_patient_id, fraction_number, treatment_date, machine_name,
                  delivered_mu, treatment_status, metadata, created_at, updated_at
        """,
        {"id": fraction_id},
    )
    return data_response(_normalize_metadata(row))


@router.get("/workflows")
def workflows(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    """List workflow rows."""

    return _list_table(
        """
        SELECT id, research_patient_id, workflow_step, workflow_status, scheduled_date, completed_date,
               metadata, updated_at
        FROM mosaiq_workflow
        ORDER BY updated_at DESC
        LIMIT :limit OFFSET :offset
        """,
        "mosaiq_workflow",
        limit,
        offset,
    )


@router.post("/workflows")
def create_workflow(payload: WorkflowCreate) -> Dict[str, Any]:
    """Create a research-side MOSAIQ workflow row."""

    values = payload.model_dump()
    values["metadata"] = _ui_metadata(values.get("metadata"))
    row = execute_returning(
        """
        INSERT INTO mosaiq_workflow (
            research_patient_id, workflow_step, workflow_status, scheduled_date, completed_date, metadata
        )
        VALUES (
            :research_patient_id, :workflow_step, :workflow_status, :scheduled_date,
            :completed_date, CAST(:metadata AS jsonb)
        )
        RETURNING id, research_patient_id, workflow_step, workflow_status, scheduled_date,
                  completed_date, metadata, created_at, updated_at
        """,
        _json_params(values),
    )
    return data_response(_normalize_metadata(row))


@router.patch("/workflows/{workflow_id}")
def update_workflow(workflow_id: int, payload: WorkflowUpdate) -> Dict[str, Any]:
    """Update a MOSAIQ workflow row."""

    row = _update_allowed(
        "mosaiq_workflow",
        workflow_id,
        payload.model_dump(exclude_unset=True),
        WORKFLOW_PATCH_FIELDS,
        WORKFLOW_COLUMNS,
    )
    return data_response(_normalize_metadata(row))


@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: int) -> Dict[str, Any]:
    """Delete a MOSAIQ workflow row."""

    row = execute_returning(
        """
        DELETE FROM mosaiq_workflow
        WHERE id = :id
        RETURNING id, research_patient_id, workflow_step, workflow_status, scheduled_date,
                  completed_date, metadata, created_at, updated_at
        """,
        {"id": workflow_id},
    )
    return data_response(_normalize_metadata(row))


def _list_table(sql: str, table: str, limit: int, offset: int) -> Dict[str, Any]:
    try:
        with get_connection() as connection:
            total = int(connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one())
            rows = connection.execute(text(sql), {"limit": limit, "offset": offset})
            return collection_response([dict(row._mapping) for row in rows], total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list %s: %s", table, exc)
        return collection_response([], total=0, limit=limit, offset=offset)


def _update_allowed(
    table_name: str,
    row_id: int,
    values: Dict[str, Any],
    allowed_fields: set,
    returning_columns: list,
) -> Dict[str, Any]:
    if table_name not in {"treatment_fraction", "mosaiq_workflow"}:
        raise ValueError(f"Unsupported table: {table_name}")
    fields = [field for field in values if field in allowed_fields]
    params: Dict[str, Any] = {"id": row_id, "ui_metadata": json.dumps(UI_METADATA)}
    assignments = ["metadata = metadata || CAST(:ui_metadata AS jsonb)"]
    for field in fields:
        value = values[field]
        if field == "metadata":
            value = json.dumps(_ui_metadata(value))
            assignments.append("metadata = metadata || CAST(:metadata AS jsonb)")
        else:
            assignments.append(f"{field} = :{field}")
        params[field] = value
    if len(assignments) == 1 and not fields:
        raise HTTPException(status_code=400, detail="No supported fields to update")
    row = execute_returning(
        f"""
        UPDATE {table_name}
        SET {", ".join(assignments)}
        WHERE id = :id
        RETURNING {", ".join(returning_columns)}
        """,
        params,
    )
    return row


def _ui_metadata(metadata: Any) -> Dict[str, Any]:
    merged = dict(metadata or {})
    merged.update(UI_METADATA)
    return merged


def _json_params(values: Dict[str, Any]) -> Dict[str, Any]:
    params = dict(values)
    params["metadata"] = json.dumps(params.get("metadata") or {})
    return params


def _normalize_metadata(row: Any) -> Any:
    if not isinstance(row, dict) or not isinstance(row.get("metadata"), str):
        return row
    normalized = dict(row)
    try:
        normalized["metadata"] = json.loads(normalized["metadata"])
    except ValueError:
        pass
    return normalized
