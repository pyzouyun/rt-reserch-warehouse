"""Research statistics endpoints."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter

from app.database import fetch_all, fetch_one
from app.schemas import data_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/statistics", tags=["statistics"])


EMPTY_SUMMARY = {"min": None, "p25": None, "median": None, "p75": None, "max": None}


@router.get("/cohort-summary")
def cohort_summary() -> Dict[str, Any]:
    """Return de-identified cohort-level baseline statistics."""

    return data_response(
        {
            "patient_count": _patient_count(),
            "sex_distribution": _rows(
                """
                SELECT COALESCE(sex, 'Unknown') AS label, count(*) AS count
                FROM patient_index
                GROUP BY COALESCE(sex, 'Unknown')
                ORDER BY count DESC, label ASC
                """
            ),
            "age_summary": _one(
                """
                SELECT
                  min(age_years) AS min,
                  percentile_cont(0.25) WITHIN GROUP (ORDER BY age_years) AS p25,
                  percentile_cont(0.50) WITHIN GROUP (ORDER BY age_years) AS median,
                  percentile_cont(0.75) WITHIN GROUP (ORDER BY age_years) AS p75,
                  max(age_years) AS max
                FROM (
                  SELECT extract(year from now())::integer - birth_year AS age_years
                  FROM patient_index
                  WHERE birth_year IS NOT NULL
                ) ages
                """
            ),
            "research_states": {
                "cohort_tags": _metadata_distribution("cohort_tag"),
                "inclusion_status": _metadata_distribution("inclusion_status"),
                "review_status": _metadata_distribution("review_status"),
            },
            "fraction_summary": _count_summary("treatment_fraction", ""),
            "cbct_summary": _count_summary("image_archive", "WHERE image_role = 'cbct'"),
            "planning_ct_summary": _count_summary("image_archive", "WHERE image_role = 'planning_ct'"),
        }
    )


@router.get("/prescription-distribution")
def prescription_distribution() -> Dict[str, Any]:
    """Return prescription, technique, site, and machine distributions."""

    return data_response(
        {
            "prescription_schemes": _rows(
                """
                SELECT prescription_dose_gy, fractions, dose_per_fraction_gy,
                       count(*) AS patient_count,
                       round(count(*) * 100.0 / NULLIF(sum(count(*)) OVER(), 0), 1) AS percentage
                FROM (
                  SELECT DISTINCT ON (research_patient_id)
                    research_patient_id, prescription_dose_gy, fractions, dose_per_fraction_gy, updated_at
                  FROM mosaiq_prescription
                  ORDER BY research_patient_id, updated_at DESC
                ) latest
                GROUP BY prescription_dose_gy, fractions, dose_per_fraction_gy
                ORDER BY patient_count DESC
                """
            ),
            "techniques": _rows(
                """
                SELECT COALESCE(technique, 'Unknown') AS label,
                       count(DISTINCT research_patient_id) AS count
                FROM mosaiq_prescription
                GROUP BY COALESCE(technique, 'Unknown')
                ORDER BY count DESC, label ASC
                """
            ),
            "treatment_sites": _rows(
                """
                SELECT COALESCE(treatment_site, 'Unknown') AS label,
                       count(DISTINCT research_patient_id) AS count
                FROM mosaiq_prescription
                GROUP BY COALESCE(treatment_site, 'Unknown')
                ORDER BY count DESC, label ASC
                """
            ),
            "machines": _rows(
                """
                SELECT COALESCE(machine_name, 'Unknown') AS machine_name,
                       count(*) AS fraction_count,
                       count(DISTINCT research_patient_id) AS patient_count
                FROM treatment_fraction
                GROUP BY COALESCE(machine_name, 'Unknown')
                ORDER BY fraction_count DESC, machine_name ASC
                """
            ),
        }
    )


@router.get("/imaging-summary")
def imaging_summary() -> Dict[str, Any]:
    """Return planning CT and CBCT archive distributions."""

    return data_response(
        {
            "by_role": _rows(
                """
                SELECT image_role AS label, count(*) AS count
                FROM image_archive
                GROUP BY image_role
                ORDER BY count DESC, label ASC
                """
            ),
            "by_source": _rows(
                """
                SELECT source_system AS label, count(*) AS count
                FROM image_archive
                GROUP BY source_system
                ORDER BY count DESC, label ASC
                """
            ),
            "per_patient": _rows(
                """
                SELECT research_patient_id,
                       count(*) FILTER (WHERE image_role = 'planning_ct') AS planning_ct_count,
                       count(*) FILTER (WHERE image_role = 'cbct') AS cbct_count,
                       count(*) FILTER (WHERE image_role = 'unknown_ct') AS unknown_ct_count,
                       max(acquisition_date) AS latest_acquisition_date
                FROM image_archive
                GROUP BY research_patient_id
                ORDER BY research_patient_id
                LIMIT 200
                """
            ),
        }
    )


def _patient_count() -> int:
    row = _one("SELECT count(*) AS patient_count FROM patient_index")
    return int(row.get("patient_count") or 0)


def _metadata_distribution(key: str) -> List[Dict[str, Any]]:
    if key not in {"cohort_tag", "inclusion_status", "review_status"}:
        raise ValueError(f"Unsupported metadata key: {key}")
    return _rows(
        f"""
        SELECT COALESCE(metadata->'research_state'->>:key, 'Unset') AS label,
               count(*) AS count
        FROM patient_index
        GROUP BY COALESCE(metadata->'research_state'->>:key, 'Unset')
        ORDER BY count DESC, label ASC
        """,
        {"key": key},
    )


def _count_summary(table_name: str, where_sql: str) -> Dict[str, Any]:
    if table_name not in {"treatment_fraction", "image_archive"}:
        raise ValueError(f"Unsupported table: {table_name}")
    return _one(
        f"""
        SELECT
          min(item_count) AS min,
          percentile_cont(0.25) WITHIN GROUP (ORDER BY item_count) AS p25,
          percentile_cont(0.50) WITHIN GROUP (ORDER BY item_count) AS median,
          percentile_cont(0.75) WITHIN GROUP (ORDER BY item_count) AS p75,
          max(item_count) AS max
        FROM (
          SELECT research_patient_id, count(*) AS item_count
          FROM {table_name}
          {where_sql}
          GROUP BY research_patient_id
        ) counts
        """
    )


def _one(sql: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    try:
        row = fetch_one(sql, params or {})
        return row or dict(EMPTY_SUMMARY)
    except Exception as exc:
        logger.warning("Statistics query failed: %s", exc)
        return dict(EMPTY_SUMMARY)


def _rows(sql: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    try:
        return fetch_all(sql, params or {})
    except Exception as exc:
        logger.warning("Statistics query failed: %s", exc)
        return []
