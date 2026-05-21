"""Dashboard endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter
from sqlalchemy import text

from app.database import get_connection, scalar_count
from app.schemas import data_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary() -> Dict[str, Any]:
    """Return high-level warehouse counts and recent ETL status."""

    return data_response(
        {
            "patients": scalar_count("patient_index"),
            "studies": scalar_count("dicom_study"),
            "series": scalar_count("dicom_series"),
            "instances": scalar_count("dicom_instance"),
            "image_archives": scalar_count("image_archive"),
            "rt_structures": scalar_count("rt_structure"),
            "rt_plans": scalar_count("rt_plan"),
            "rt_doses": scalar_count("rt_dose"),
            "fractions": scalar_count("treatment_fraction"),
            "workflows": scalar_count("mosaiq_workflow"),
            "modalities": _modalities(),
            "recent_etl": _recent_etl(),
        }
    )


def _modalities() -> List[Dict[str, Any]]:
    try:
        with get_connection() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT COALESCE(modality, 'UNKNOWN') AS modality, count(*) AS count
                    FROM dicom_instance
                    GROUP BY COALESCE(modality, 'UNKNOWN')
                    ORDER BY count DESC, modality ASC
                    LIMIT 12
                    """
                )
            )
            return [dict(row._mapping) for row in rows]
    except Exception as exc:
        logger.warning("Could not load modality summary: %s", exc)
        return []


def _recent_etl() -> List[Dict[str, Any]]:
    try:
        with get_connection() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT pipeline_name, status, message, records_processed, created_at
                    FROM etl_log
                    ORDER BY created_at DESC
                    LIMIT 5
                    """
                )
            )
            return [dict(row._mapping) for row in rows]
    except Exception as exc:
        logger.warning("Could not load recent ETL rows: %s", exc)
        return []
