# Research UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a research management dashboard UI for the radiotherapy data warehouse.

**Architecture:** Add a FastAPI service as the read-only API boundary over PostgreSQL and controlled ETL commands, then add a React/Vite frontend for dashboard, patient index, DICOM browser, RT data, MOSAIQ data, and ETL console. Docker Compose runs API and web services alongside Orthanc/PostgreSQL.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, React, TypeScript, Vite, lucide-react, CSS.

---

### Task 1: API Test Skeleton

**Files:**
- Create: `api/tests/test_api.py`
- Create: `api/app/__init__.py`

**Steps:**
1. Add tests for `/api/v1/health`, `/api/v1/dashboard/summary`, and `/api/v1/patients`.
2. Verify tests fail because API modules do not exist.
3. Implement minimal FastAPI app, database helpers, and dashboard/patient routes.
4. Run API tests.

### Task 2: API Resources

**Files:**
- Create: `api/app/database.py`
- Create: `api/app/main.py`
- Create: `api/app/routers/*.py`
- Create: `api/requirements.txt`
- Create: `api/Dockerfile`

**Steps:**
1. Add REST endpoints under `/api/v1`.
2. Use limit/offset pagination for list endpoints.
3. Return only de-identified fields.
4. Add controlled ETL trigger endpoints.

### Task 3: Frontend App

**Files:**
- Create: `web/package.json`
- Create: `web/src/*`
- Create: `web/Dockerfile`

**Steps:**
1. Build a high-density research admin layout.
2. Add pages for Dashboard, Patients, DICOM, RT Data, MOSAIQ, ETL Console, Security.
3. Use reusable API client, table, status, and metric components.
4. Keep UI responsive and avoid PHI display.

### Task 4: Compose And Docs

**Files:**
- Modify: `docker-compose.yml`
- Modify: `Makefile`
- Modify: `.env.example`
- Modify: `README.md`
- Create: `docs/ui_guide.md`

**Steps:**
1. Add `api` and `web` services.
2. Add make targets for UI and API tests.
3. Document usage and extension points.

### Task 5: Verification

**Steps:**
1. Run API tests.
2. Run Python compile check.
3. Run Docker Compose config validation.
4. If frontend dependencies are available, run frontend build.
