"""DICOM browsing endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database import get_connection
from app.schemas import collection_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dicom", tags=["dicom"])


@router.get("/series")
def list_series(
    modality: Optional[str] = Query(default=None, max_length=32),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List DICOM series with study and patient context."""

    where = "WHERE s.modality = :modality" if modality else ""
    params = {"modality": modality, "limit": limit, "offset": offset}
    try:
        with get_connection() as connection:
            total = int(connection.execute(text(f"SELECT count(*) FROM dicom_series s {where}"), params).scalar_one())
            rows = connection.execute(
                text(
                    f"""
                    SELECT
                        pi.research_patient_id,
                        st.study_date,
                        st.study_description,
                        s.series_instance_uid_hash,
                        s.modality,
                        s.series_number,
                        s.series_description,
                        s.updated_at
                    FROM dicom_series s
                    JOIN dicom_study st ON st.id = s.dicom_study_id
                    JOIN patient_index pi ON pi.id = st.patient_index_id
                    {where}
                    ORDER BY s.updated_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            )
            return collection_response([dict(row._mapping) for row in rows], total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list DICOM series: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)


@router.get("/instances")
def list_instances(
    modality: Optional[str] = Query(default=None, max_length=32),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List DICOM instances."""

    where = "WHERE i.modality = :modality" if modality else ""
    params = {"modality": modality, "limit": limit, "offset": offset}
    try:
        with get_connection() as connection:
            total = int(connection.execute(text(f"SELECT count(*) FROM dicom_instance i {where}"), params).scalar_one())
            rows = connection.execute(
                text(
                    f"""
                    SELECT
                        i.sop_instance_uid_hash,
                        i.sop_class_uid,
                        i.modality,
                        i.instance_number,
                        i.orthanc_instance_id,
                        i.updated_at
                    FROM dicom_instance i
                    {where}
                    ORDER BY i.updated_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                params,
            )
            return collection_response([dict(row._mapping) for row in rows], total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list DICOM instances: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)
