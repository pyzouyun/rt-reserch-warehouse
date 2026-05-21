# Database Schema

All tables include `created_at` and `updated_at`. Direct identifiers such as patient name, national ID, phone, and address are not stored.

## Core DICOM Tables

- `patient_index`: pseudonymous `research_patient_id`, salted `patient_id_hash`, optional non-identifying demographics.
- `dicom_study`: hashed StudyInstanceUID and study-level metadata.
- `dicom_series`: hashed SeriesInstanceUID, modality, series number, frame of reference hash.
- `dicom_instance`: hashed SOPInstanceUID, SOP class, Orthanc instance id.
- `image_archive`: one row per archived CT-like DICOM Series, classifying planning CT, XVI CBCT, or unknown CT while preserving only hashed identifiers and non-identifying metadata.

## Radiotherapy Tables

- `rt_structure`: RTSTRUCT summary and ROI metadata in JSON.
- `rt_plan`: RTPLAN summary, beams, fractions, approval status, prescription placeholders.
- `rt_dose`: RTDOSE summary and dose grid metadata.
- `dvh_metric`: ROI-level DVH metrics such as Dmean, Dmax, Dmin, D95, V5 through V50.

## Treatment And Workflow Tables

- `treatment_fraction`: MOSAIQ or linac-derived fraction delivery rows.
- `mosaiq_prescription`: prescription rows imported from MOSAIQ CSV exports.
- `xvi_registration`: DICOM REG/RTIMAGE/CBCT-derived registration summaries and future XVI log imports.
- `mosaiq_workflow`: workflow states imported from CSV.
- `clinical_outcome`: manually curated or registry-derived outcome endpoints.
- `etl_log`: pipeline status, counts, and diagnostic messages.

## Indexing

Indexes cover hashed identifiers, modality, dates, patient-level joins, DVH ROI queries, workflow steps, and ETL status queries.
