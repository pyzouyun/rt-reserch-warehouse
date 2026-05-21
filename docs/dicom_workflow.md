# Monaco, XVI, and Elekta DICOM Workflow

## Orthanc Receiver

- AE Title: `RT_RESEARCH`
- Host: Docker host IP or server DNS name
- DICOM C-STORE port: `4242`
- REST/Web port: `8042`

## Monaco

Configure a DICOM export destination pointing to `RT_RESEARCH`. Export planning CT, RTSTRUCT, RTPLAN, and RTDOSE as read-only research copies. Keep Monaco as the source of truth for clinical planning.

## XVI / CBCT

Send CBCT DICOM series, registration objects if available, and RTIMAGE/REG exports to Orthanc. CT-like series are archived into `image_archive` during ETL:

- `planning_ct`: planning or simulation CT exported from Monaco or CT simulation workflows.
- `cbct`: XVI/Elekta cone-beam CT series.
- `unknown_ct`: CT series that do not match the current planning CT or CBCT rules.

One patient can have multiple planning CT series and multiple CBCT series. The archive is one row per DICOM Series; raw image files remain in Orthanc.

## Elekta Linac

For DICOM objects, send or export them to Orthanc. For non-DICOM delivery logs, place approved read-only copies in `logs/linac/` and add a parser after the export format is confirmed.

## Validation

Use the Orthanc web UI to confirm received studies, then run:

```bash
make etl
```
