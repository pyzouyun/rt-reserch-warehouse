# Overall Architecture

## Components

- Orthanc receives DICOM C-STORE traffic on AE Title `RT_RESEARCH`, port `4242`, and exposes REST on port `8042`.
- PostgreSQL stores research-ready structured metadata, pseudonymous patient indexes, RT object summaries, fraction records, workflow rows, outcomes, and ETL logs.
- Python ETL reads from Orthanc REST, parses DICOM objects with pydicom, hashes identifiers, and upserts metadata into PostgreSQL.
- MOSAIQ is represented by CSV templates first, avoiding assumptions about production database access.
- Elekta linac and XVI non-DICOM logs are reserved under `logs/` for future read-only parser modules.

## Data Flow

1. Monaco, XVI, or another DICOM node sends CT, CBCT, RTSTRUCT, RTPLAN, RTDOSE, RTIMAGE, or REG objects to Orthanc.
2. `etl.run_etl` scans Orthanc instances through REST.
3. ETL parses only required metadata and writes salted hashes plus pseudonymous keys to PostgreSQL.
4. MOSAIQ CSV exports are imported through `etl.import_mosaiq_csv`.
5. Researchers query PostgreSQL, not clinical systems.

## Boundaries

The warehouse is read-only relative to clinical systems. It must not send modified DICOM, treatment parameters, approvals, or workflow changes back to Monaco, MOSAIQ, XVI, or linac systems.
