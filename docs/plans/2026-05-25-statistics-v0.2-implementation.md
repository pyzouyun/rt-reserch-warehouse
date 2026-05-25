# Statistics v0.2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add research statistics APIs, patient-level CSV export, and a statistics workbench page for existing de-identified warehouse data.

**Architecture:** FastAPI exposes read-only statistics and export routers backed by PostgreSQL aggregation queries. React adds a Statistics page using existing cards and tables. No clinical source system is modified, and no direct identifiers are returned.

**Tech Stack:** FastAPI, SQLAlchemy text queries, PostgreSQL, React/Vite/TypeScript.

---

### Task 1: Backend Tests

Add tests for:

- `/api/v1/statistics/cohort-summary`
- `/api/v1/statistics/prescription-distribution`
- `/api/v1/statistics/imaging-summary`
- `/api/v1/export/patients-csv`

### Task 2: Backend Routers

Create:

- `api/app/routers/statistics.py`
- `api/app/routers/export.py`

Register both in `api/app/main.py`.

### Task 3: Frontend Types and Page

Modify:

- `web/src/api.ts`
- `web/src/App.tsx`

Add a `统计` navigation page with tables and CSV export action.

### Task 4: Docs and Release Notes

Create:

- `docs/statistics_v0.2_technical_design.md`
- `docs/releases/v0.2.0-statistics.md`

Update:

- `README.md`
- `docs/usage_guide.md`

### Task 5: Verification

Run:

- `C:\Users\zy\miniconda3\python.exe -m pytest tests api/tests -q`
- `C:\Users\zy\miniconda3\python.exe -m compileall -q etl api\app`
- `npm run build`
- `docker compose config --quiet`
