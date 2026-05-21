"""Shared API response helpers and request models."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def data_response(data: Any) -> Dict[str, Any]:
    """Wrap a resource response in a standard envelope."""

    return {"data": data}


def collection_response(data: List[Dict[str, Any]], *, total: int, limit: int, offset: int) -> Dict[str, Any]:
    """Wrap collection data with pagination metadata."""

    return {
        "data": data,
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        },
    }


class ClinicalOutcomeCreate(BaseModel):
    """Create payload for de-identified clinical outcomes."""

    research_patient_id: str = Field(..., min_length=1, max_length=128)
    outcome_type: str = Field(..., min_length=1, max_length=128)
    outcome_date: Optional[date] = None
    outcome_value: Optional[str] = Field(default=None, max_length=512)
    grade: Optional[str] = Field(default=None, max_length=64)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClinicalOutcomeUpdate(BaseModel):
    """Patch payload for clinical outcomes."""

    outcome_type: Optional[str] = Field(default=None, min_length=1, max_length=128)
    outcome_date: Optional[date] = None
    outcome_value: Optional[str] = Field(default=None, max_length=512)
    grade: Optional[str] = Field(default=None, max_length=64)
    metadata: Optional[Dict[str, Any]] = None


class PatientResearchStateUpdate(BaseModel):
    """Research queue metadata stored under patient_index.metadata.research_state."""

    cohort_tag: Optional[str] = Field(default=None, max_length=128)
    inclusion_status: Optional[str] = Field(default=None, max_length=128)
    review_status: Optional[str] = Field(default=None, max_length=128)
    research_note: Optional[str] = Field(default=None, max_length=2000)


class TreatmentFractionCreate(BaseModel):
    """Create payload for research-side treatment fraction rows."""

    research_patient_id: str = Field(..., min_length=1, max_length=128)
    fraction_number: Optional[int] = None
    treatment_date: Optional[date] = None
    machine_name: Optional[str] = Field(default=None, max_length=128)
    delivered_mu: Optional[Decimal] = None
    treatment_status: Optional[str] = Field(default=None, max_length=128)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TreatmentFractionUpdate(BaseModel):
    """Patch payload for treatment fractions."""

    fraction_number: Optional[int] = None
    treatment_date: Optional[date] = None
    machine_name: Optional[str] = Field(default=None, max_length=128)
    delivered_mu: Optional[Decimal] = None
    treatment_status: Optional[str] = Field(default=None, max_length=128)
    metadata: Optional[Dict[str, Any]] = None


class WorkflowCreate(BaseModel):
    """Create payload for research-side MOSAIQ workflow rows."""

    research_patient_id: str = Field(..., min_length=1, max_length=128)
    workflow_step: str = Field(..., min_length=1, max_length=128)
    workflow_status: Optional[str] = Field(default=None, max_length=128)
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    """Patch payload for MOSAIQ workflow rows."""

    workflow_step: Optional[str] = Field(default=None, min_length=1, max_length=128)
    workflow_status: Optional[str] = Field(default=None, max_length=128)
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None
