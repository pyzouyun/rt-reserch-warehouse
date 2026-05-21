CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE patient_index (
    id bigserial PRIMARY KEY,
    research_patient_id text NOT NULL UNIQUE,
    patient_id_hash text NOT NULL,
    patient_name_present boolean NOT NULL DEFAULT false,
    sex text,
    birth_year integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE dicom_study (
    id bigserial PRIMARY KEY,
    patient_index_id bigint NOT NULL REFERENCES patient_index(id) ON DELETE CASCADE,
    study_instance_uid_hash text NOT NULL UNIQUE,
    accession_number_hash text,
    study_date date,
    study_description text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE dicom_series (
    id bigserial PRIMARY KEY,
    dicom_study_id bigint NOT NULL REFERENCES dicom_study(id) ON DELETE CASCADE,
    series_instance_uid_hash text NOT NULL UNIQUE,
    modality text,
    series_number integer,
    series_description text,
    frame_of_reference_uid_hash text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE dicom_instance (
    id bigserial PRIMARY KEY,
    dicom_series_id bigint NOT NULL REFERENCES dicom_series(id) ON DELETE CASCADE,
    sop_instance_uid_hash text NOT NULL UNIQUE,
    sop_class_uid text,
    modality text,
    instance_number integer,
    orthanc_instance_id text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE image_archive (
    id bigserial PRIMARY KEY,
    research_patient_id text NOT NULL,
    dicom_series_id bigint NOT NULL UNIQUE REFERENCES dicom_series(id) ON DELETE CASCADE,
    image_role text NOT NULL,
    source_system text NOT NULL DEFAULT 'Unknown',
    acquisition_date date,
    acquisition_time text,
    series_instance_uid_hash text NOT NULL,
    frame_of_reference_uid_hash text,
    study_description text,
    series_description text,
    orthanc_instance_id text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rt_structure (
    id bigserial PRIMARY KEY,
    dicom_instance_id bigint NOT NULL UNIQUE REFERENCES dicom_instance(id) ON DELETE CASCADE,
    structure_set_label text,
    structure_count integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rt_plan (
    id bigserial PRIMARY KEY,
    dicom_instance_id bigint NOT NULL UNIQUE REFERENCES dicom_instance(id) ON DELETE CASCADE,
    plan_label text,
    plan_name text,
    approval_status text,
    prescribed_dose_gy numeric,
    fractions_planned integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rt_dose (
    id bigserial PRIMARY KEY,
    dicom_instance_id bigint NOT NULL UNIQUE REFERENCES dicom_instance(id) ON DELETE CASCADE,
    dose_summation_type text,
    dose_type text,
    dose_units text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE dvh_metric (
    id bigserial PRIMARY KEY,
    research_patient_id text NOT NULL,
    rt_structure_id bigint REFERENCES rt_structure(id) ON DELETE CASCADE,
    rt_dose_id bigint REFERENCES rt_dose(id) ON DELETE CASCADE,
    roi_name text NOT NULL,
    metric_name text NOT NULL,
    metric_value numeric NOT NULL,
    metric_unit text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (research_patient_id, rt_structure_id, rt_dose_id, roi_name, metric_name)
);

CREATE TABLE treatment_fraction (
    id bigserial PRIMARY KEY,
    research_patient_id text NOT NULL,
    fraction_number integer,
    treatment_date date,
    machine_name text,
    delivered_mu numeric,
    treatment_status text,
    source_record_hash text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE mosaiq_prescription (
    id bigserial PRIMARY KEY,
    research_patient_id text NOT NULL,
    course_id_hash text,
    plan_id_hash text,
    prescription_dose_gy numeric,
    fractions integer,
    dose_per_fraction_gy numeric,
    treatment_site text,
    technique text,
    source_record_hash text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE xvi_registration (
    id bigserial PRIMARY KEY,
    dicom_instance_id bigint UNIQUE REFERENCES dicom_instance(id) ON DELETE SET NULL,
    research_patient_id text,
    registration_type text,
    registration_uid_hash text,
    couch_shift_lateral_mm numeric,
    couch_shift_longitudinal_mm numeric,
    couch_shift_vertical_mm numeric,
    rotation_pitch_deg numeric,
    rotation_roll_deg numeric,
    rotation_yaw_deg numeric,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE mosaiq_workflow (
    id bigserial PRIMARY KEY,
    research_patient_id text NOT NULL,
    workflow_step text NOT NULL,
    workflow_status text,
    scheduled_date date,
    completed_date date,
    source_record_hash text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE clinical_outcome (
    id bigserial PRIMARY KEY,
    research_patient_id text NOT NULL,
    outcome_type text NOT NULL,
    outcome_date date,
    outcome_value text,
    grade text,
    source_record_hash text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE etl_log (
    id bigserial PRIMARY KEY,
    pipeline_name text NOT NULL,
    status text NOT NULL,
    message text,
    records_processed integer NOT NULL DEFAULT 0,
    started_at timestamptz,
    finished_at timestamptz,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_patient_index_patient_hash ON patient_index(patient_id_hash);
CREATE INDEX idx_dicom_study_patient ON dicom_study(patient_index_id);
CREATE INDEX idx_dicom_study_date ON dicom_study(study_date);
CREATE INDEX idx_dicom_series_study ON dicom_series(dicom_study_id);
CREATE INDEX idx_dicom_series_modality ON dicom_series(modality);
CREATE INDEX idx_dicom_instance_series ON dicom_instance(dicom_series_id);
CREATE INDEX idx_dicom_instance_orthanc ON dicom_instance(orthanc_instance_id);
CREATE INDEX idx_image_archive_patient_role ON image_archive(research_patient_id, image_role);
CREATE INDEX idx_image_archive_acquisition_date ON image_archive(acquisition_date);
CREATE INDEX idx_image_archive_series_hash ON image_archive(series_instance_uid_hash);
CREATE INDEX idx_dvh_metric_patient_roi ON dvh_metric(research_patient_id, roi_name);
CREATE INDEX idx_treatment_fraction_patient_date ON treatment_fraction(research_patient_id, treatment_date);
CREATE INDEX idx_mosaiq_prescription_patient ON mosaiq_prescription(research_patient_id);
CREATE INDEX idx_xvi_registration_patient ON xvi_registration(research_patient_id);
CREATE INDEX idx_mosaiq_workflow_patient_step ON mosaiq_workflow(research_patient_id, workflow_step);
CREATE INDEX idx_clinical_outcome_patient_type ON clinical_outcome(research_patient_id, outcome_type);
CREATE INDEX idx_etl_log_pipeline_status ON etl_log(pipeline_name, status);

CREATE TRIGGER trg_patient_index_updated_at BEFORE UPDATE ON patient_index FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_dicom_study_updated_at BEFORE UPDATE ON dicom_study FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_dicom_series_updated_at BEFORE UPDATE ON dicom_series FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_dicom_instance_updated_at BEFORE UPDATE ON dicom_instance FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_image_archive_updated_at BEFORE UPDATE ON image_archive FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_rt_structure_updated_at BEFORE UPDATE ON rt_structure FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_rt_plan_updated_at BEFORE UPDATE ON rt_plan FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_rt_dose_updated_at BEFORE UPDATE ON rt_dose FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_dvh_metric_updated_at BEFORE UPDATE ON dvh_metric FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_treatment_fraction_updated_at BEFORE UPDATE ON treatment_fraction FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_mosaiq_prescription_updated_at BEFORE UPDATE ON mosaiq_prescription FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_xvi_registration_updated_at BEFORE UPDATE ON xvi_registration FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_mosaiq_workflow_updated_at BEFORE UPDATE ON mosaiq_workflow FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_clinical_outcome_updated_at BEFORE UPDATE ON clinical_outcome FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_etl_log_updated_at BEFORE UPDATE ON etl_log FOR EACH ROW EXECUTE FUNCTION set_updated_at();
