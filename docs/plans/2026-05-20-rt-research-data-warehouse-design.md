# RT Research Data Warehouse Design

The prototype uses Orthanc as the DICOM ingress and archive, PostgreSQL as the research metadata warehouse, and Python 3.11 ETL jobs as read-only processors. Clinical systems remain source systems only: Monaco, MOSAIQ, Elekta linac, and XVI send or export data into the warehouse path, and no component writes back to them.

The first implementation is intentionally small: it stores DICOM identity fields only as salted hashes, creates a pseudonymous `research_patient_id`, parses core CT/CBCT/RTSTRUCT/RTPLAN/RTDOSE metadata, exposes a dicompyler-core DVH extraction interface, and imports MOSAIQ-style CSV files. Non-DICOM linac and XVI logs are reserved landing zones for later site-specific parsers.

Testing focuses on the highest-risk behavior in the prototype: stable salted de-identification and safe non-identifying DICOM metadata parsing.
