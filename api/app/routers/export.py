"""De-identified CSV export endpoints."""

from __future__ import annotations

import csv
from io import StringIO
from typing import Any, Dict, Iterable, List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.database import fetch_all

router = APIRouter(prefix="/export", tags=["export"])

PATIENT_COLUMNS = [
    "research_patient_id",
    "sex",
    "birth_year",
    "cohort_tag",
    "inclusion_status",
    "review_status",
    "treatment_site",
    "technique",
    "prescription_dose_gy",
    "fractions",
    "dose_per_fraction_gy",
    "fraction_count",
    "planning_ct_count",
    "cbct_count",
    "unknown_ct_count",
]


@router.get("/patients-csv")
def patients_csv() -> StreamingResponse:
    """Export one de-identified row per research patient."""

    rows = fetch_all(_patients_csv_sql(), {})
    return StreamingResponse(
        _csv_lines(rows, PATIENT_COLUMNS),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=rt_research_patients.csv"},
    )


def _csv_lines(rows: List[Dict[str, Any]], columns: List[str]) -> Iterable[str]:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


def _patients_csv_sql() -> str:
    return """
    WITH latest_prescription AS (
      SELECT DISTINCT ON (research_patient_id)
        research_patient_id, treatment_site, technique, prescription_dose_gy,
        fractions, dose_per_fraction_gy
      FROM mosaiq_prescription
      ORDER BY research_patient_id, updated_at DESC
    ),
    fraction_counts AS (
      SELECT research_patient_id, count(*) AS fraction_count
      FROM treatment_fraction
      GROUP BY research_patient_id
    ),
    image_counts AS (
      SELECT research_patient_id,
             count(*) FILTER (WHERE image_role = 'planning_ct') AS planning_ct_count,
             count(*) FILTER (WHERE image_role = 'cbct') AS cbct_count,
             count(*) FILTER (WHERE image_role = 'unknown_ct') AS unknown_ct_count
      FROM image_archive
      GROUP BY research_patient_id
    )
    SELECT
      pi.research_patient_id,
      pi.sex,
      pi.birth_year,
      pi.metadata->'research_state'->>'cohort_tag' AS cohort_tag,
      pi.metadata->'research_state'->>'inclusion_status' AS inclusion_status,
      pi.metadata->'research_state'->>'review_status' AS review_status,
      lp.treatment_site,
      lp.technique,
      lp.prescription_dose_gy,
      lp.fractions,
      lp.dose_per_fraction_gy,
      COALESCE(fc.fraction_count, 0) AS fraction_count,
      COALESCE(ic.planning_ct_count, 0) AS planning_ct_count,
      COALESCE(ic.cbct_count, 0) AS cbct_count,
      COALESCE(ic.unknown_ct_count, 0) AS unknown_ct_count
    FROM patient_index pi
    LEFT JOIN latest_prescription lp ON lp.research_patient_id = pi.research_patient_id
    LEFT JOIN fraction_counts fc ON fc.research_patient_id = pi.research_patient_id
    LEFT JOIN image_counts ic ON ic.research_patient_id = pi.research_patient_id
    ORDER BY pi.research_patient_id
    """
