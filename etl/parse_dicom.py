"""Minimal DICOM and DICOM-RT metadata parsing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
from typing import Any, Dict, List, Optional

from pydicom.dataset import Dataset
from pydicom.uid import UID

from etl.deidentify import hash_identifier, research_patient_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PatientRecord:
    research_patient_id: str
    patient_id_hash: str
    patient_name_present: bool


@dataclass(frozen=True)
class StudyRecord:
    study_instance_uid_hash: str
    study_date: Optional[date]
    accession_number_hash: Optional[str]
    study_description: Optional[str]


@dataclass(frozen=True)
class SeriesRecord:
    series_instance_uid_hash: str
    modality: Optional[str]
    series_number: Optional[int]
    series_description: Optional[str]
    frame_of_reference_uid_hash: Optional[str]


@dataclass(frozen=True)
class InstanceRecord:
    sop_instance_uid_hash: str
    sop_class_uid: Optional[str]
    modality: Optional[str]
    instance_number: Optional[int]
    orthanc_instance_id: Optional[str]


@dataclass(frozen=True)
class ImageArchiveRecord:
    research_patient_id: str
    image_role: str
    source_system: str
    acquisition_date: Optional[date]
    acquisition_time: Optional[str]
    series_instance_uid_hash: str
    frame_of_reference_uid_hash: Optional[str]
    study_description: Optional[str]
    series_description: Optional[str]
    orthanc_instance_id: Optional[str]
    metadata: Dict[str, Any]


@dataclass(frozen=True)
class ParsedDicom:
    patient: PatientRecord
    study: StudyRecord
    series: SeriesRecord
    instance: InstanceRecord
    rt_structure: Optional[Dict[str, Any]]
    rt_plan: Optional[Dict[str, Any]]
    rt_dose: Optional[Dict[str, Any]]
    xvi_registration: Optional[Dict[str, Any]]
    image_archive: Optional[ImageArchiveRecord]


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dicom_date(value: Any) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y%m%d").date()
    except ValueError:
        logger.debug("Could not parse DICOM date %s", value)
        return None


def _hash(value: Any, salt: str) -> Optional[str]:
    if value in (None, ""):
        return None
    return hash_identifier(value, salt=salt)


def parse_dataset(dataset: Dataset, *, salt: str, orthanc_instance_id: Optional[str] = None) -> ParsedDicom:
    """Parse a DICOM dataset into non-identifying warehouse records."""

    patient_id = getattr(dataset, "PatientID", None)
    modality = str(getattr(dataset, "Modality", "") or "")

    rt_structure = _parse_rt_structure(dataset, salt=salt) if modality == "RTSTRUCT" else None
    rt_plan = _parse_rt_plan(dataset) if modality == "RTPLAN" else None
    rt_dose = _parse_rt_dose(dataset) if modality == "RTDOSE" else None
    xvi_registration = _parse_registration(dataset, salt=salt) if modality in {"REG", "RTIMAGE", "CT"} else None
    patient_research_id = research_patient_id(patient_id, salt=salt)
    series_uid_hash = hash_identifier(getattr(dataset, "SeriesInstanceUID", None), salt=salt)
    frame_uid_hash = _hash(getattr(dataset, "FrameOfReferenceUID", None), salt)
    study_description = getattr(dataset, "StudyDescription", None)
    series_description = getattr(dataset, "SeriesDescription", None)
    image_archive = _parse_image_archive(
        dataset,
        salt=salt,
        research_patient_id_value=patient_research_id,
        series_instance_uid_hash=series_uid_hash,
        frame_of_reference_uid_hash=frame_uid_hash,
        study_description=study_description,
        series_description=series_description,
        orthanc_instance_id=orthanc_instance_id,
    )

    return ParsedDicom(
        patient=PatientRecord(
            research_patient_id=patient_research_id,
            patient_id_hash=hash_identifier(patient_id, salt=salt),
            patient_name_present=hasattr(dataset, "PatientName"),
        ),
        study=StudyRecord(
            study_instance_uid_hash=hash_identifier(getattr(dataset, "StudyInstanceUID", None), salt=salt),
            study_date=_dicom_date(getattr(dataset, "StudyDate", None)),
            accession_number_hash=_hash(getattr(dataset, "AccessionNumber", None), salt),
            study_description=study_description,
        ),
        series=SeriesRecord(
            series_instance_uid_hash=series_uid_hash,
            modality=modality or None,
            series_number=_as_int(getattr(dataset, "SeriesNumber", None)),
            series_description=series_description,
            frame_of_reference_uid_hash=frame_uid_hash,
        ),
        instance=InstanceRecord(
            sop_instance_uid_hash=hash_identifier(getattr(dataset, "SOPInstanceUID", None), salt=salt),
            sop_class_uid=str(getattr(dataset, "SOPClassUID", "")) or None,
            modality=modality or None,
            instance_number=_as_int(getattr(dataset, "InstanceNumber", None)),
            orthanc_instance_id=orthanc_instance_id,
        ),
        rt_structure=rt_structure,
        rt_plan=rt_plan,
        rt_dose=rt_dose,
        xvi_registration=xvi_registration,
        image_archive=image_archive,
    )


def _parse_rt_structure(dataset: Dataset, *, salt: str) -> Dict[str, Any]:
    roi_names: List[str] = []
    for roi in getattr(dataset, "StructureSetROISequence", []) or []:
        name = getattr(roi, "ROIName", None)
        if name:
            roi_names.append(str(name))
    return {
        "structure_set_label": getattr(dataset, "StructureSetLabel", None),
        "structure_count": len(roi_names),
        "roi_names": roi_names,
        "referenced_frame_uid_hash": _hash(getattr(dataset, "FrameOfReferenceUID", None), salt),
    }


def _parse_rt_plan(dataset: Dataset) -> Dict[str, Any]:
    beams = getattr(dataset, "BeamSequence", []) or []
    fraction_groups = getattr(dataset, "FractionGroupSequence", []) or []
    prescribed_dose = None
    fractions = None
    if fraction_groups:
        group = fraction_groups[0]
        fractions = _as_int(getattr(group, "NumberOfFractionsPlanned", None))
    return {
        "plan_label": getattr(dataset, "RTPlanLabel", None),
        "plan_name": getattr(dataset, "RTPlanName", None),
        "approval_status": getattr(dataset, "ApprovalStatus", None),
        "beam_count": len(beams),
        "fractions_planned": fractions,
        "prescribed_dose_gy": prescribed_dose,
    }


def _parse_rt_dose(dataset: Dataset) -> Dict[str, Any]:
    return {
        "dose_summation_type": getattr(dataset, "DoseSummationType", None),
        "dose_type": getattr(dataset, "DoseType", None),
        "dose_units": getattr(dataset, "DoseUnits", None),
        "grid_scaling": float(getattr(dataset, "DoseGridScaling", 0.0) or 0.0),
    }


def _parse_registration(dataset: Dataset, *, salt: str) -> Optional[Dict[str, Any]]:
    description = f"{getattr(dataset, 'SeriesDescription', '')} {getattr(dataset, 'ProtocolName', '')}".lower()
    manufacturer = str(getattr(dataset, "Manufacturer", "")).lower()
    if "xvi" not in description and "elekta" not in manufacturer and getattr(dataset, "Modality", None) != "REG":
        return None
    return {
        "registration_type": getattr(dataset, "Modality", None),
        "registration_uid_hash": _hash(getattr(dataset, "SOPInstanceUID", None), salt),
        "raw_metadata": {
            "series_description": getattr(dataset, "SeriesDescription", None),
            "protocol_name": getattr(dataset, "ProtocolName", None),
            "manufacturer": getattr(dataset, "Manufacturer", None),
        },
    }


def _parse_image_archive(
    dataset: Dataset,
    *,
    salt: str,
    research_patient_id_value: str,
    series_instance_uid_hash: str,
    frame_of_reference_uid_hash: Optional[str],
    study_description: Optional[str],
    series_description: Optional[str],
    orthanc_instance_id: Optional[str],
) -> Optional[ImageArchiveRecord]:
    if str(getattr(dataset, "Modality", "") or "") != "CT":
        return None
    descriptor = " ".join(
        str(value or "")
        for value in (
            study_description,
            series_description,
            getattr(dataset, "ProtocolName", None),
            getattr(dataset, "Manufacturer", None),
            getattr(dataset, "ManufacturerModelName", None),
            getattr(dataset, "StationName", None),
        )
    ).lower()
    image_role = _classify_ct_role(descriptor)
    source_system = _classify_source_system(descriptor, image_role)
    return ImageArchiveRecord(
        research_patient_id=research_patient_id_value,
        image_role=image_role,
        source_system=source_system,
        acquisition_date=_dicom_date(getattr(dataset, "AcquisitionDate", None))
        or _dicom_date(getattr(dataset, "SeriesDate", None))
        or _dicom_date(getattr(dataset, "StudyDate", None)),
        acquisition_time=str(getattr(dataset, "AcquisitionTime", "") or getattr(dataset, "SeriesTime", "") or "") or None,
        series_instance_uid_hash=series_instance_uid_hash,
        frame_of_reference_uid_hash=frame_of_reference_uid_hash,
        study_description=study_description,
        series_description=series_description,
        orthanc_instance_id=orthanc_instance_id,
        metadata={
            "protocol_name": getattr(dataset, "ProtocolName", None),
            "manufacturer": getattr(dataset, "Manufacturer", None),
            "manufacturer_model_name": getattr(dataset, "ManufacturerModelName", None),
            "station_name": getattr(dataset, "StationName", None),
            "classification_text_hash": _hash(descriptor, salt),
        },
    )


def _classify_ct_role(descriptor: str) -> str:
    cbct_markers = ("cbct", "xvi", "cone beam", "conebeam", "kvct", "kvcbct", "volumeview")
    planning_markers = ("planning", "plan ct", "simulation", "sim ct", "ct sim", "定位", "monaco")
    if any(marker in descriptor for marker in cbct_markers):
        return "cbct"
    if any(marker in descriptor for marker in planning_markers):
        return "planning_ct"
    return "unknown_ct"


def _classify_source_system(descriptor: str, image_role: str) -> str:
    if "xvi" in descriptor:
        return "XVI"
    if "elekta" in descriptor and image_role == "cbct":
        return "XVI"
    if "monaco" in descriptor or image_role == "planning_ct":
        return "Monaco"
    if "elekta" in descriptor:
        return "Elekta"
    return "Unknown"


def sop_class_name(uid: Optional[Any]) -> Optional[str]:
    """Return a human-readable SOP class name when pydicom knows it."""

    if not uid:
        return None
    try:
        return UID(str(uid)).name
    except Exception:
        logger.debug("Unknown SOP class UID %s", uid)
        return None
