# Non-DICOM Log Landing Zone

This prototype does not parse proprietary Elekta linac or XVI text/binary logs yet.

- `logs/linac/`: reserve for accelerator delivery logs, trajectory logs, QA exports, or service-approved read-only copies.
- `logs/xvi/`: reserve for XVI registration exports, CBCT workflow logs, or registration summaries.

Recommended next step: define a site-specific export contract, copy logs into these folders read-only, hash direct identifiers, then add parser modules under `etl/` that load normalized records into `treatment_fraction` and `xvi_registration`.
