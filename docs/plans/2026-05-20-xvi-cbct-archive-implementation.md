# XVI CBCT Archive Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a research-side image archive for Monaco planning CT and XVI/Elekta CBCT series, supporting multiple CT and CBCT series per patient.

**Architecture:** Orthanc remains the DICOM storage source. ETL classifies CT-like DICOM series into a PostgreSQL `image_archive` table keyed by hashed series identity, while API and Web UI expose read-only archive browsing. No data is written back to Monaco, MOSAIQ, XVI, or Elekta systems.

**Tech Stack:** PostgreSQL, Python 3.11, pydicom, SQLAlchemy, FastAPI, React/Vite.

---

### Task 1: Classification Tests

**Files:**
- Modify: `tests/test_parse_dicom.py`

**Steps:**
1. Add tests for planning CT and XVI CBCT classification from DICOM tags.
2. Run `python -m pytest tests/test_parse_dicom.py -q` and confirm failure before implementation.

### Task 2: Database Migration

**Files:**
- Create: `sql/002_image_archive.sql`
- Modify: `sql/001_init.sql`

**Steps:**
1. Add `image_archive` table with one row per DICOM series archive record.
2. Add indexes for patient, role, acquisition date, and series hash.
3. Add trigger for `updated_at`.

### Task 3: ETL Archive Upsert

**Files:**
- Modify: `etl/parse_dicom.py`
- Modify: `etl/load_to_db.py`

**Steps:**
1. Add `ImageArchiveRecord` dataclass.
2. Classify CT series into `planning_ct`, `cbct`, or `unknown_ct`.
3. Upsert one archive row per DICOM series.

### Task 4: API

**Files:**
- Create: `api/app/routers/xvi.py`
- Modify: `api/app/main.py`
- Modify: `api/tests/test_api.py`

**Steps:**
1. Add `/api/v1/xvi/image-archive`.
2. Add `/api/v1/xvi/cbct-series`.
3. Return patient, role, source system, dates, series hash, descriptions, frame hash, and instance count.

### Task 5: Web UI

**Files:**
- Modify: `web/src/api.ts`
- Modify: `web/src/App.tsx`

**Steps:**
1. Add `XVI/CBCT` navigation item.
2. Add filters for patient and image role.
3. Show planning CT and CBCT archive rows.

### Task 6: Docs and Verification

**Files:**
- Create: `docs/xvi_cbct_archive.md`
- Modify: `docs/dicom_workflow.md`
- Modify: `docs/database_schema.md`
- Modify: `docs/usage_guide.md`

**Commands:**
- `C:\Users\zy\miniconda3\python.exe -m pytest tests api/tests -q`
- `C:\Users\zy\miniconda3\python.exe -m compileall -q etl api\app`
- `npm run build` in `web/`
- `docker compose config`
- Apply `sql/002_image_archive.sql` to the running PostgreSQL container when Docker is available.
