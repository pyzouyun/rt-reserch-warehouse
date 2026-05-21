# Research Workbench V2 Design

## Goal

Build a second version of the radiotherapy research workbench that supports core operational actions from the UI, while preserving the project's clinical safety boundary: clinical-source DICOM and treatment-system data remain read-only, and editable behavior is limited to research-side records.

## Scope

V2 should turn the current display-oriented UI into an operational research workspace with:

- Data import actions.
- Patient research queue management.
- Clinical outcome CRUD.
- Research-side MOSAIQ workflow and fraction CRUD.
- ETL task controls and logs.
- Detail drawers or forms for common records.

The system must not write back to Monaco, MOSAIQ, XVI, Elekta accelerators, or source DICOM objects.

## Editing Boundary

Read-only:

- DICOM studies, series, and instances.
- RTSTRUCT, RTPLAN, RTDOSE, and parsed DVH records.
- Orthanc stored DICOM objects, except future explicitly designed archive cleanup operations.

Editable in V2:

- `clinical_outcome`
- Research-side workflow rows in `mosaiq_workflow`
- Research-side treatment fraction rows in `treatment_fraction`
- Research queue fields added to `patient_index.metadata`, such as inclusion status, cohort tag, review status, and free-text research note.
- Import job metadata and ETL task records.

Delete behavior should be conservative. Prefer soft delete for research-side rows where possible, implemented using metadata flags in V2 if schema migration is kept minimal.

## Recommended User Workflows

### Dashboard

Add a top action bar:

- Run Orthanc ETL.
- Import MOSAIQ CSV.
- Open DICOM receive settings.
- Open latest ETL logs.

Add system status cards:

- API status.
- PostgreSQL status.
- Orthanc status.
- Last ETL result.

### Patient Research Queue

Current patient table should become a working list:

- Search by `research_patient_id`.
- Filter by cohort tag, inclusion status, and review status.
- Open patient detail.
- Edit research note, cohort tag, inclusion/exclusion status, and review status.
- Create clinical outcome for the patient.

No patient name or direct identifier is displayed or editable.

### Patient Detail

A patient detail drawer or page should show:

- DICOM studies and series.
- RT objects and DVH metrics.
- MOSAIQ prescription, fractions, and workflow rows.
- Clinical outcomes.
- Research notes and queue status.

Actions:

- Add outcome.
- Edit outcome.
- Delete or soft-delete outcome.
- Add workflow row.
- Add treatment fraction row.
- Run patient-focused ETL in the future.

### MOSAIQ Import Center

Replace the current passive MOSAIQ tables with an import center:

- Show required CSV templates.
- Upload or choose CSV files.
- Validate CSV headers.
- Preview first rows.
- Import.
- Show import result and errors.

Docker mode can initially support importing from mounted `data_templates/`. Browser file upload can be added if the API writes temporary upload files.

### Clinical Outcome Management

Add full CRUD for research outcomes:

- Create outcome for `research_patient_id`.
- List outcomes.
- Edit outcome type, date, value, grade, and metadata.
- Delete or soft-delete row.

This is the safest first CRUD target because it is clearly research-side data.

### ETL Task Center

Expand ETL page:

- Run Orthanc ETL.
- Import MOSAIQ CSV.
- Future: extract DVH.
- Future: parse XVI registration logs.
- Show command output.
- Show paginated `etl_log`.
- Filter by pipeline and status.

## API Design

Add write endpoints under `/api/v1`.

Suggested routes:

```text
GET    /patients
GET    /patients/{research_patient_id}
PATCH  /patients/{research_patient_id}/research-state

GET    /outcomes
POST   /outcomes
GET    /outcomes/{id}
PATCH  /outcomes/{id}
DELETE /outcomes/{id}

GET    /mosaiq/fractions
POST   /mosaiq/fractions
PATCH  /mosaiq/fractions/{id}
DELETE /mosaiq/fractions/{id}

GET    /mosaiq/workflows
POST   /mosaiq/workflows
PATCH  /mosaiq/workflows/{id}
DELETE /mosaiq/workflows/{id}

POST   /imports/mosaiq/validate
POST   /imports/mosaiq/run
GET    /etl/logs
POST   /etl/run-orthanc
POST   /etl/import-mosaiq
```

Use Pydantic schemas for request validation. All free-text fields should be treated as research notes and must reject obvious direct identifiers only if a validation policy is implemented. At minimum, UI copy must warn not to enter PHI.

## Database Strategy

Keep V2 low-risk by using existing tables first:

- Use `patient_index.metadata` for research queue fields.
- Use `clinical_outcome` for outcomes.
- Use `treatment_fraction` and `mosaiq_workflow` for research-side edits.
- Use `etl_log` for task visibility.

Optional migration for V2.1:

- Add `deleted_at` and `deleted_reason` to research-side editable tables.
- Add `operation_audit_log` for UI write operations.
- Add `import_batch` table to group CSV imports.

For V2, if no migration is added, DELETE can be real delete only for manually entered research-side rows. DICOM-derived tables should not have delete endpoints.

## Frontend Design

Keep the current admin layout, but add operational controls:

- Top action bar on each page.
- Detail drawer for selected rows.
- Modal forms for create/edit.
- Confirmation dialog for delete.
- Toast or inline result banners for API success/failure.

New or revised pages:

- Dashboard: status and quick actions.
- Patients: research queue with edit state and detail drawer.
- DICOM: read-only browser plus receive settings.
- RT Data: read-only browser plus future DVH task action.
- MOSAIQ: import center plus editable research-side tables.
- Outcomes: full CRUD page.
- ETL: task center and logs.
- Security: write-boundary explanation and PHI warning.

## Error Handling

- API returns `400` for validation errors.
- API returns `404` for missing editable rows.
- API returns `409` for unsafe operations, such as trying to edit a read-only DICOM-derived table.
- UI should display actionable error messages and keep form data intact after failure.

## Testing

Backend:

- Add API tests for create/update/delete outcome.
- Add API tests for patient research-state patch.
- Add API tests for workflow and fraction create/update/delete.
- Add safety tests confirming DICOM/RT records have no write endpoints.

Frontend:

- Build check with `npm run build`.
- Add lightweight component or interaction tests later if a frontend test runner is introduced.

Manual:

- Run Docker stack.
- Create a research outcome.
- Edit patient inclusion status.
- Run ETL from the UI.
- Import MOSAIQ CSV from the UI or mounted template.
- Confirm DICOM/RT data remains read-only.

## Open Questions

- Should V2 use hard delete for manually created research rows, or introduce `deleted_at` now?
- Should browser CSV upload be supported immediately, or should V2 continue using mounted `data_templates/`?
- Should authentication be added in V2, or kept as a later production-hardening task?
