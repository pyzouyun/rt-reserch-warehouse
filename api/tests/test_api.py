import json

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_service_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_summary_has_core_counts() -> None:
    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert "patients" in payload
    assert "studies" in payload
    assert "series" in payload
    assert "instances" in payload
    assert "modalities" in payload
    assert "image_archives" in payload


def test_patients_endpoint_returns_collection_envelope() -> None:
    response = client.get("/api/v1/patients?limit=10&offset=0")

    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    assert "meta" in payload
    assert payload["meta"]["limit"] == 10


def test_research_workbench_request_models_import() -> None:
    from app.schemas import (
        ClinicalOutcomeCreate,
        ClinicalOutcomeUpdate,
        PatientResearchStateUpdate,
        TreatmentFractionCreate,
        TreatmentFractionUpdate,
        WorkflowCreate,
        WorkflowUpdate,
    )

    assert ClinicalOutcomeCreate(research_patient_id="RP-1", outcome_type="survival")
    assert ClinicalOutcomeUpdate(outcome_value="stable")
    assert PatientResearchStateUpdate(cohort_tag="lung-qc")
    assert TreatmentFractionCreate(research_patient_id="RP-1")
    assert TreatmentFractionUpdate(treatment_status="Treated")
    assert WorkflowCreate(research_patient_id="RP-1", workflow_step="CT simulation")
    assert WorkflowUpdate(workflow_status="Completed")


def test_outcomes_crud_endpoints(monkeypatch) -> None:
    from app.routers import outcomes

    outcome = {
        "id": 7,
        "research_patient_id": "RP-1",
        "outcome_type": "toxicity",
        "outcome_date": "2026-01-03",
        "outcome_value": "dermatitis",
        "grade": "2",
        "metadata": {"source": "ui"},
    }

    monkeypatch.setattr(outcomes, "fetch_all", lambda sql, params: [outcome])
    monkeypatch.setattr(outcomes, "fetch_one", lambda sql, params: outcome)
    monkeypatch.setattr(outcomes, "execute_returning", lambda sql, params: {**outcome, **params})

    list_response = client.get("/api/v1/outcomes?limit=10&offset=0")
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["id"] == 7

    create_response = client.post(
        "/api/v1/outcomes",
        json={
            "research_patient_id": "RP-1",
            "outcome_type": "toxicity",
            "outcome_date": "2026-01-03",
            "outcome_value": "dermatitis",
            "grade": "2",
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["data"]["research_patient_id"] == "RP-1"

    detail_response = client.get("/api/v1/outcomes/7")
    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == 7

    patch_response = client.patch("/api/v1/outcomes/7", json={"grade": "1"})
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["grade"] == "1"

    delete_response = client.delete("/api/v1/outcomes/7")
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["id"] == 7


def test_patient_research_state_patch_merges_metadata(monkeypatch) -> None:
    from app.routers import patients

    captured = {}

    def fake_execute_returning(sql, params):
        captured.update(params)
        return {
            "research_patient_id": params["research_patient_id"],
            "metadata": {"existing": True, "research_state": params["research_state"]},
        }

    monkeypatch.setattr(patients, "execute_returning", fake_execute_returning)

    response = client.patch(
        "/api/v1/patients/RP-1/research-state",
        json={
            "cohort_tag": "lung-qc",
            "inclusion_status": "included",
            "review_status": "needs_review",
            "research_note": "Imported from pilot cohort",
        },
    )

    assert response.status_code == 200
    metadata = response.json()["data"]["metadata"]
    assert metadata["existing"] is True
    assert metadata["research_state"]["cohort_tag"] == "lung-qc"
    assert captured["research_state"]["review_status"] == "needs_review"


def test_mosaiq_fraction_and_workflow_write_endpoints(monkeypatch) -> None:
    from app.routers import mosaiq

    calls = []

    def fake_execute_returning(sql, params):
        calls.append(params)
        return {**params, "id": params.get("id", 11)}

    monkeypatch.setattr(mosaiq, "execute_returning", fake_execute_returning)

    fraction_response = client.post(
        "/api/v1/mosaiq/fractions",
        json={"research_patient_id": "RP-1", "fraction_number": 1, "treatment_status": "Treated"},
    )
    assert fraction_response.status_code == 200
    assert fraction_response.json()["data"]["metadata"]["source"] == "ui"
    assert fraction_response.json()["data"]["metadata"]["editable"] is True

    patch_fraction = client.patch("/api/v1/mosaiq/fractions/11", json={"treatment_status": "Reviewed"})
    assert patch_fraction.status_code == 200

    delete_fraction = client.delete("/api/v1/mosaiq/fractions/11")
    assert delete_fraction.status_code == 200

    workflow_response = client.post(
        "/api/v1/mosaiq/workflows",
        json={"research_patient_id": "RP-1", "workflow_step": "CT simulation", "workflow_status": "Scheduled"},
    )
    assert workflow_response.status_code == 200
    assert workflow_response.json()["data"]["metadata"]["source"] == "ui"

    patch_workflow = client.patch("/api/v1/mosaiq/workflows/11", json={"workflow_status": "Completed"})
    assert patch_workflow.status_code == 200

    delete_workflow = client.delete("/api/v1/mosaiq/workflows/11")
    assert delete_workflow.status_code == 200
    assert any(_metadata(call).get("editable") is True for call in calls)


def test_mosaiq_import_validate_and_run(tmp_path, monkeypatch) -> None:
    from app.routers import imports

    templates = {
        "mosaiq_patient.csv": "PatientID,Sex,BirthYear\nRP-1,F,1965\n",
        "mosaiq_prescription.csv": "PatientID,CourseID,PlanID,PrescriptionDoseGy,Fractions,DosePerFractionGy\nRP-1,C1,P1,50,25,2\n",
        "mosaiq_fraction.csv": "PatientID,CourseID,PlanID,FractionNumber,TreatmentDate,MachineName,DeliveredMU,Status\nRP-1,C1,P1,1,2026-01-03,LINAC,100,Treated\n",
        "mosaiq_workflow.csv": "PatientID,CourseID,WorkflowStep,Status,ScheduledDate,CompletedDate\nRP-1,C1,CT simulation,Done,2026-01-01,2026-01-01\n",
    }
    for name, content in templates.items():
        (tmp_path / name).write_text(content)

    monkeypatch.setenv("MOSAIQ_CSV_DIR", str(tmp_path))

    validate_response = client.post("/api/v1/imports/mosaiq/validate")
    assert validate_response.status_code == 200
    assert validate_response.json()["data"]["valid"] is True
    assert validate_response.json()["data"]["missing_files"] == []

    class Result:
        returncode = 0
        stdout = "imported"
        stderr = ""

    monkeypatch.setattr(imports.subprocess, "run", lambda *args, **kwargs: Result())

    run_response = client.post("/api/v1/imports/mosaiq/run")
    assert run_response.status_code == 200
    assert run_response.json()["data"]["exit_code"] == 0


def test_xvi_image_archive_endpoints(monkeypatch) -> None:
    from app.routers import xvi

    rows = [
        {
            "research_patient_id": "RP-1",
            "image_role": "cbct",
            "source_system": "XVI",
            "acquisition_date": "2026-01-03",
            "series_description": "XVI CBCT Fraction 03",
            "series_instance_uid_hash": "series-hash",
            "instance_count": 120,
        }
    ]

    monkeypatch.setattr(xvi, "fetch_all", lambda sql, params: rows)
    monkeypatch.setattr(xvi, "fetch_one", lambda sql, params: {"total": 1})

    archive_response = client.get("/api/v1/xvi/image-archive?image_role=cbct")
    assert archive_response.status_code == 200
    assert archive_response.json()["data"][0]["image_role"] == "cbct"
    assert archive_response.json()["data"][0]["instance_count"] == 120

    cbct_response = client.get("/api/v1/xvi/cbct-series")
    assert cbct_response.status_code == 200
    assert cbct_response.json()["data"][0]["source_system"] == "XVI"


def test_statistics_endpoints_return_research_summaries(monkeypatch) -> None:
    from app.routers import statistics

    def fake_fetch_one(sql, params):
        if "count(*) AS patient_count" in sql:
            return {"patient_count": 3}
        return {"min": 1, "p25": 1, "median": 2, "p75": 3, "max": 4}

    def fake_fetch_all(sql, params):
        if "sex" in sql:
            return [{"label": "F", "count": 2}, {"label": "M", "count": 1}]
        if "image_role" in sql:
            return [{"label": "cbct", "count": 5}]
        return [{"label": "HeadNeck", "count": 3}]

    monkeypatch.setattr(statistics, "fetch_one", fake_fetch_one)
    monkeypatch.setattr(statistics, "fetch_all", fake_fetch_all)

    cohort = client.get("/api/v1/statistics/cohort-summary")
    assert cohort.status_code == 200
    assert cohort.json()["data"]["patient_count"] == 3
    assert cohort.json()["data"]["sex_distribution"][0]["label"] == "F"
    assert "cbct_summary" in cohort.json()["data"]

    prescription = client.get("/api/v1/statistics/prescription-distribution")
    assert prescription.status_code == 200
    assert "prescription_schemes" in prescription.json()["data"]
    assert "machines" in prescription.json()["data"]

    imaging = client.get("/api/v1/statistics/imaging-summary")
    assert imaging.status_code == 200
    assert imaging.json()["data"]["by_role"][0]["label"] == "cbct"


def test_patient_csv_export_returns_deidentified_csv(monkeypatch) -> None:
    from app.routers import export

    rows = [
        {
            "research_patient_id": "RP-1",
            "sex": "F",
            "birth_year": 1970,
            "cohort_tag": "pilot",
            "inclusion_status": "included",
            "review_status": "reviewed",
            "treatment_site": "HeadNeck",
            "technique": "VMAT",
            "prescription_dose_gy": 52.5,
            "fractions": 15,
            "dose_per_fraction_gy": 3.5,
            "fraction_count": 15,
            "planning_ct_count": 1,
            "cbct_count": 0,
            "unknown_ct_count": 0,
        }
    ]
    monkeypatch.setattr(export, "fetch_all", lambda sql, params: rows)

    response = client.get("/api/v1/export/patients-csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    body = response.text
    assert "research_patient_id" in body
    assert "RP-1" in body
    assert "PatientName" not in body


def _metadata(call):
    metadata = call.get("metadata", {})
    if isinstance(metadata, str):
        return json.loads(metadata)
    return metadata
