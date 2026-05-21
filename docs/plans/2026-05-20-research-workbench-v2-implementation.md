# Research Workbench V2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add core import and research-side CRUD actions to the radiotherapy research workbench.

**Architecture:** Extend the FastAPI service with validated write endpoints only for research-side data, while keeping DICOM and RT parsed data read-only. Extend the React/Vite UI with action bars, modal forms, row actions, and detail views that call the new API endpoints.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy text queries, PostgreSQL, React, TypeScript, Vite, lucide-react, CSS.

---

### Task 1: Backend CRUD Schemas And Helpers

**Files:**
- Modify: `api/app/schemas.py`
- Modify: `api/app/database.py`
- Test: `api/tests/test_api.py`

**Step 1: Add failing schema/import tests**

Add tests that import request models for outcome create/update and patient research-state update.

Expected models:

```python
ClinicalOutcomeCreate
ClinicalOutcomeUpdate
PatientResearchStateUpdate
TreatmentFractionCreate
TreatmentFractionUpdate
WorkflowCreate
WorkflowUpdate
```

Run:

```powershell
C:\Users\zy\miniconda3\python.exe -m pytest api/tests -q
```

Expected: fail because models do not exist.

**Step 2: Implement Pydantic models**

In `api/app/schemas.py`, add typed Pydantic models. Allow optional fields for patch models. Keep fields de-identified.

**Step 3: Add database row helpers**

In `api/app/database.py`, add helpers:

```python
def fetch_one(sql: str, params: dict[str, Any]) -> dict[str, Any] | None
def fetch_all(sql: str, params: dict[str, Any]) -> list[dict[str, Any]]
def execute_returning(sql: str, params: dict[str, Any]) -> dict[str, Any] | None
```

Use Python 3.8-compatible typing if legacy support must remain.

**Step 4: Run tests**

Run:

```powershell
C:\Users\zy\miniconda3\python.exe -m pytest api/tests -q
```

Expected: pass.

### Task 2: Clinical Outcome API

**Files:**
- Create: `api/app/routers/outcomes.py`
- Modify: `api/app/main.py`
- Test: `api/tests/test_api.py`

**Step 1: Write failing endpoint tests**

Add tests for:

- `GET /api/v1/outcomes`
- `POST /api/v1/outcomes`
- `PATCH /api/v1/outcomes/{id}`
- `DELETE /api/v1/outcomes/{id}`

Mock or use safe empty-database behavior consistent with current tests.

**Step 2: Implement router**

Create endpoints:

```text
GET    /outcomes
POST   /outcomes
GET    /outcomes/{id}
PATCH  /outcomes/{id}
DELETE /outcomes/{id}
```

Use `clinical_outcome`. Return standard `data_response` and `collection_response`.

**Step 3: Register router**

Modify `api/app/main.py` to include `outcomes.router`.

**Step 4: Verify**

Run:

```powershell
C:\Users\zy\miniconda3\python.exe -m pytest api/tests -q
```

### Task 3: Patient Research State API

**Files:**
- Modify: `api/app/routers/patients.py`
- Test: `api/tests/test_api.py`

**Step 1: Write failing tests**

Test:

```text
PATCH /api/v1/patients/{research_patient_id}/research-state
```

Payload:

```json
{
  "cohort_tag": "lung-qc",
  "inclusion_status": "included",
  "review_status": "needs_review",
  "research_note": "Imported from pilot cohort"
}
```

Expected: response includes updated `metadata.research_state`.

**Step 2: Implement endpoint**

Update `patient_index.metadata` using `jsonb_set` or merge operator. Keep existing metadata keys.

**Step 3: Verify**

Run API tests.

### Task 4: Workflow And Fraction Research-Side API

**Files:**
- Modify: `api/app/routers/mosaiq.py`
- Test: `api/tests/test_api.py`

**Step 1: Add failing tests**

Cover create/update/delete for:

```text
POST   /api/v1/mosaiq/fractions
PATCH  /api/v1/mosaiq/fractions/{id}
DELETE /api/v1/mosaiq/fractions/{id}
POST   /api/v1/mosaiq/workflows
PATCH  /api/v1/mosaiq/workflows/{id}
DELETE /api/v1/mosaiq/workflows/{id}
```

**Step 2: Implement write endpoints**

Use existing `treatment_fraction` and `mosaiq_workflow` tables.

**Step 3: Add source metadata**

For manual UI rows, write:

```json
{"source": "ui", "editable": true}
```

inside `metadata`.

**Step 4: Verify**

Run API tests.

### Task 5: MOSAIQ Import Action API

**Files:**
- Create: `api/app/routers/imports.py`
- Modify: `api/app/main.py`
- Test: `api/tests/test_api.py`

**Step 1: Add tests**

Test:

```text
POST /api/v1/imports/mosaiq/validate
POST /api/v1/imports/mosaiq/run
```

**Step 2: Implement validate**

Read expected CSV template files from configured `MOSAIQ_CSV_DIR` or `/app/data_templates`. Validate required filenames and headers. Return missing files and header errors.

**Step 3: Implement run**

Reuse existing subprocess command:

```python
[sys.executable, "-m", "etl.import_mosaiq_csv"]
```

**Step 4: Verify**

Run API tests.

### Task 6: Frontend API Client Extensions

**Files:**
- Modify: `web/src/api.ts`

**Step 1: Add TypeScript types**

Add types for:

```typescript
ClinicalOutcome
ClinicalOutcomeInput
PatientResearchState
WorkflowInput
FractionInput
ImportValidationResult
```

**Step 2: Add helper functions**

Add wrappers around `fetchJson`:

```typescript
apiGet
apiPost
apiPatch
apiDelete
```

**Step 3: Build**

Run:

```powershell
cd web
npm run build
```

### Task 7: Shared UI Controls

**Files:**
- Modify: `web/src/components.tsx`
- Modify: `web/src/styles.css`

**Step 1: Add reusable components**

Add:

```typescript
ActionButton
ConfirmButton
Modal
FormRow
InlineAlert
RowActions
```

Use lucide icons. Keep button dimensions stable and compact.

**Step 2: Build**

Run frontend build.

### Task 8: Outcomes Page

**Files:**
- Modify: `web/src/App.tsx`

**Step 1: Add navigation item**

Add page key:

```typescript
"outcomes"
```

Label: `结局`

**Step 2: Implement list/create/edit/delete**

Use modal form with fields:

```text
research_patient_id
outcome_type
outcome_date
outcome_value
grade
```

**Step 3: Build**

Run frontend build.

### Task 9: Patient Queue Actions

**Files:**
- Modify: `web/src/App.tsx`

**Step 1: Add patient row actions**

Actions:

- Detail
- 编辑研究状态
- 新增结局

**Step 2: Add detail drawer**

Show patient detail from `/patients/{research_patient_id}`.

**Step 3: Add research state modal**

Patch `/patients/{research_patient_id}/research-state`.

**Step 4: Build**

Run frontend build.

### Task 10: MOSAIQ Import And Editable Tables

**Files:**
- Modify: `web/src/App.tsx`

**Step 1: Add import center actions**

Buttons:

- 校验 CSV
- 导入 CSV
- 刷新结果

**Step 2: Add workflow/fraction row actions**

Add create/edit/delete actions for research-side rows.

**Step 3: Build**

Run frontend build.

### Task 11: Safety Copy And Docs

**Files:**
- Modify: `docs/ui_guide.md`
- Modify: `docs/user_manual_docker.md`
- Modify: `docs/user_manual_legacy_windows.md`
- Create: `docs/research_workbench_v2.md`

**Step 1: Document editable boundary**

State clearly:

- DICOM/RT clinical-source data is read-only.
- Research-side outcome, workflow, fraction, and queue metadata can be edited.
- No write-back to clinical systems.

**Step 2: Document workflows**

Add screenshots later if desired; for now document button paths and expected behavior.

### Task 12: Final Verification

**Files:**
- No code changes unless verification finds issues.

**Step 1: Run API tests**

```powershell
C:\Users\zy\miniconda3\python.exe -m pytest tests api/tests -q
```

**Step 2: Run Python compile check**

```powershell
C:\Users\zy\miniconda3\python.exe -m compileall -q etl api\app
```

**Step 3: Run frontend build**

```powershell
cd web
npm run build
```

**Step 4: Run Docker Compose config check**

```powershell
docker compose config
```

**Step 5: Manual smoke test**

Start stack:

```powershell
docker compose up -d postgres orthanc api web
```

Open:

```text
http://localhost:8080
```

Verify:

- Outcomes page loads.
- Create/edit/delete outcome.
- Edit patient research state.
- Validate/import MOSAIQ CSV.
- Run Orthanc ETL.
- DICOM and RT pages remain read-only.
