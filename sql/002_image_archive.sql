CREATE TABLE IF NOT EXISTS image_archive (
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

CREATE INDEX IF NOT EXISTS idx_image_archive_patient_role ON image_archive(research_patient_id, image_role);
CREATE INDEX IF NOT EXISTS idx_image_archive_acquisition_date ON image_archive(acquisition_date);
CREATE INDEX IF NOT EXISTS idx_image_archive_series_hash ON image_archive(series_instance_uid_hash);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_image_archive_updated_at'
    ) THEN
        CREATE TRIGGER trg_image_archive_updated_at
        BEFORE UPDATE ON image_archive
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    END IF;
END $$;
