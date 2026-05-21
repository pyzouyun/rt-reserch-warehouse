"""Radiotherapy data endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database import get_connection
from app.schemas import collection_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rt", tags=["rt"])


@router.get("/objects")
def list_rt_objects(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    """List RTSTRUCT, RTPLAN, and RTDOSE records in one feed."""

    sql = """
        SELECT 'RTSTRUCT' AS object_type, i.sop_instance_uid_hash, i.orthanc_instance_id, rs.metadata, rs.updated_at
        FROM rt_structure rs JOIN dicom_instance i ON i.id = rs.dicom_instance_id
        UNION ALL
        SELECT 'RTPLAN' AS object_type, i.sop_instance_uid_hash, i.orthanc_instance_id, rp.metadata, rp.updated_at
        FROM rt_plan rp JOIN dicom_instance i ON i.id = rp.dicom_instance_id
        UNION ALL
        SELECT 'RTDOSE' AS object_type, i.sop_instance_uid_hash, i.orthanc_instance_id, rd.metadata, rd.updated_at
        FROM rt_dose rd JOIN dicom_instance i ON i.id = rd.dicom_instance_id
    """
    try:
        with get_connection() as connection:
            total = int(connection.execute(text(f"SELECT count(*) FROM ({sql}) rt_objects")).scalar_one())
            rows = connection.execute(
                text(f"SELECT * FROM ({sql}) rt_objects ORDER BY updated_at DESC LIMIT :limit OFFSET :offset"),
                {"limit": limit, "offset": offset},
            )
            return collection_response([dict(row._mapping) for row in rows], total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list RT objects: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)


@router.get("/dvh-metrics")
def list_dvh_metrics(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)) -> Dict[str, Any]:
    """List DVH metrics."""

    try:
        with get_connection() as connection:
            total = int(connection.execute(text("SELECT count(*) FROM dvh_metric")).scalar_one())
            rows = connection.execute(
                text(
                    """
                    SELECT research_patient_id, roi_name, metric_name, metric_value, metric_unit, updated_at
                    FROM dvh_metric
                    ORDER BY updated_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": limit, "offset": offset},
            )
            return collection_response([dict(row._mapping) for row in rows], total=total, limit=limit, offset=offset)
    except Exception as exc:
        logger.warning("Could not list DVH metrics: %s", exc)
        return collection_response([], total=0, limit=limit, offset=offset)
