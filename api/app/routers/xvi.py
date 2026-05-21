"""XVI and CBCT image archive endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

from app.database import fetch_all, fetch_one
from app.schemas import collection_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/xvi", tags=["xvi"])


@router.get("/image-archive")
def image_archive(
    research_patient_id: Optional[str] = Query(default=None, max_length=128),
    image_role: Optional[str] = Query(default=None, max_length=32),
    limit: int = Query(default=80, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List archived planning CT and CBCT series."""

    where_sql, params = _filters(research_patient_id, image_role)
    params.update({"limit": limit, "offset": offset})
    try:
        rows = fetch_all(
            f"""
            SELECT
                ia.id,
                ia.research_patient_id,
                ia.image_role,
                ia.source_system,
                ia.acquisition_date,
                ia.acquisition_time,
                ia.series_instance_uid_hash,
                ia.frame_of_reference_uid_hash,
                ia.study_description,
                ia.series_description,
                ia.orthanc_instance_id,
                ia.metadata,
                ia.updated_at,
                COALESCE(inst.instance_count, 0) AS instance_count
            FROM image_archive ia
            LEFT JOIN (
                SELECT dicom_series_id, count(*) AS instance_count
                FROM dicom_instance
                GROUP BY dicom_series_id
            ) inst ON inst.dicom_series_id = ia.dicom_series_id
            {where_sql}
            ORDER BY ia.acquisition_date DESC NULLS LAST, ia.updated_at DESC
            LIMIT :limit OFFSET :offset
            """,
            params,
        )
        return collection_response(rows, total=_archive_count(where_sql, params), limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list image archive rows: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)


@router.get("/cbct-series")
def cbct_series(
    research_patient_id: Optional[str] = Query(default=None, max_length=128),
    limit: int = Query(default=80, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List XVI/Elekta CBCT archive rows."""

    return image_archive(
        research_patient_id=research_patient_id,
        image_role="cbct",
        limit=limit,
        offset=offset,
    )


def _filters(research_patient_id: Optional[str], image_role: Optional[str]) -> tuple[str, Dict[str, Any]]:
    clauses = []
    params: Dict[str, Any] = {}
    if research_patient_id:
        clauses.append("ia.research_patient_id = :research_patient_id")
        params["research_patient_id"] = research_patient_id
    if image_role:
        clauses.append("ia.image_role = :image_role")
        params["image_role"] = image_role
    return ("WHERE " + " AND ".join(clauses), params) if clauses else ("", params)


def _archive_count(where_sql: str, params: Dict[str, Any]) -> int:
    row = fetch_one(f"SELECT count(*) AS total FROM image_archive ia {where_sql}", params)
    return int(row["total"]) if row is not None else 0
