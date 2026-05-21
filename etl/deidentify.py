"""DICOM de-identification helpers."""

from __future__ import annotations

import hashlib
import logging
from typing import Iterable, Optional, Tuple

from pydicom.dataset import Dataset

logger = logging.getLogger(__name__)

DIRECT_IDENTIFIER_TAGS: Tuple[str, ...] = (
    "PatientName",
    "PatientBirthDate",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "OtherPatientIDs",
    "OtherPatientNames",
    "InstitutionAddress",
    "ReferringPhysicianName",
)


def hash_identifier(value: Optional[object], *, salt: str) -> str:
    """Return a salted SHA-256 hash for an identifier-like value."""

    normalized = "" if value is None else str(value).strip()
    payload = f"{salt}:{normalized}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def research_patient_id(patient_id: Optional[object], *, salt: str) -> str:
    """Create a stable pseudonymous patient key suitable for research joins."""

    return f"RP-{hash_identifier(patient_id, salt=salt)[:16].upper()}"


def deidentify_dataset(dataset: Dataset, *, salt: str, keep_tags: Optional[Iterable[str]] = None) -> Dataset:
    """Return a copied dataset with direct identifiers removed or replaced."""

    keep = set(keep_tags or ())
    cleaned = dataset.copy()
    patient_id = getattr(cleaned, "PatientID", None)
    cleaned.PatientID = research_patient_id(patient_id, salt=salt)

    for keyword in DIRECT_IDENTIFIER_TAGS:
        if keyword in keep:
            continue
        if hasattr(cleaned, keyword):
            delattr(cleaned, keyword)

    logger.debug("De-identified dataset for research patient id %s", cleaned.PatientID)
    return cleaned
