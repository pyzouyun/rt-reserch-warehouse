from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import CTImageStorage, ExplicitVRLittleEndian

from etl.parse_dicom import parse_dataset


def make_minimal_dataset() -> Dataset:
    dataset = Dataset()
    dataset.file_meta = FileMetaDataset()
    dataset.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset.file_meta.MediaStorageSOPClassUID = CTImageStorage
    dataset.PatientID = "P001"
    dataset.PatientName = "Sensitive^Name"
    dataset.StudyInstanceUID = "1.2.3"
    dataset.SeriesInstanceUID = "1.2.3.4"
    dataset.SOPInstanceUID = "1.2.3.4.5"
    dataset.SOPClassUID = CTImageStorage
    dataset.Modality = "CT"
    dataset.StudyDate = "20260102"
    dataset.SeriesDescription = "Planning CT"
    dataset.InstanceNumber = 7
    return dataset


def test_parse_dataset_extracts_non_identifying_dicom_metadata() -> None:
    parsed = parse_dataset(make_minimal_dataset(), salt="site-secret")

    assert parsed.patient.research_patient_id.startswith("RP-")
    assert parsed.patient.patient_id_hash
    assert parsed.patient.patient_name_present is True
    assert parsed.study.study_instance_uid_hash
    assert parsed.series.modality == "CT"
    assert parsed.instance.sop_instance_uid_hash
    assert parsed.instance.instance_number == 7


def test_parse_dataset_classifies_planning_ct_for_image_archive() -> None:
    dataset = make_minimal_dataset()
    dataset.SeriesDescription = "Planning CT 1.0mm"
    dataset.ProtocolName = "SIMULATION"
    dataset.AcquisitionDate = "20260103"
    dataset.AcquisitionTime = "101530"
    dataset.FrameOfReferenceUID = "1.2.840.1"

    parsed = parse_dataset(dataset, salt="site-secret")

    assert parsed.image_archive is not None
    assert parsed.image_archive.image_role == "planning_ct"
    assert parsed.image_archive.source_system == "Monaco"
    assert parsed.image_archive.acquisition_date.isoformat() == "2026-01-03"
    assert parsed.image_archive.acquisition_time == "101530"
    assert parsed.image_archive.series_instance_uid_hash == parsed.series.series_instance_uid_hash
    assert parsed.image_archive.frame_of_reference_uid_hash == parsed.series.frame_of_reference_uid_hash


def test_parse_dataset_classifies_xvi_cbct_for_image_archive() -> None:
    dataset = make_minimal_dataset()
    dataset.SeriesInstanceUID = "1.2.3.4.9"
    dataset.SOPInstanceUID = "1.2.3.4.9.1"
    dataset.SeriesDescription = "XVI CBCT Fraction 03"
    dataset.ProtocolName = "Cone Beam Head"
    dataset.Manufacturer = "Elekta"

    parsed = parse_dataset(dataset, salt="site-secret", orthanc_instance_id="orthanc-1")

    assert parsed.image_archive is not None
    assert parsed.image_archive.image_role == "cbct"
    assert parsed.image_archive.source_system == "XVI"
    assert parsed.image_archive.orthanc_instance_id == "orthanc-1"
