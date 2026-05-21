# Security And De-Identification

## De-Identification Rules

- `PatientID`, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID, accession number, and frame of reference UID are stored as salted SHA-256 hashes.
- `research_patient_id` is derived from salted PatientID hash and does not expose the source identifier.
- Patient name, national ID, phone, address, and similar direct identifiers are not stored.
- DICOM files remain in Orthanc storage; research tables store metadata only.

## Operational Controls

- Replace all values in `.env.example` before production use.
- Use a long random `DEIDENTIFY_SALT`; keep it outside code and backups shared with researchers.
- Restrict Orthanc and PostgreSQL ports to trusted network segments.
- Use role-based database access for researchers.
- Review CSV exports before import, especially free-text columns.

## Ethics

Use this warehouse only under institutional approval, data use agreements, and IRB/ethics review where required. Keep a documented data dictionary, access log, retention policy, and process for removing records when consent or authorization changes.
