const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export interface CollectionResponse<T> {
  data: T[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

export interface DataResponse<T> {
  data: T;
}

export interface DashboardSummary {
  patients: number;
  studies: number;
  series: number;
  instances: number;
  rt_structures: number;
  rt_plans: number;
  rt_doses: number;
  image_archives: number;
  fractions: number;
  workflows: number;
  modalities: Array<{ modality: string; count: number }>;
  recent_etl: EtlLog[];
}

export interface PatientRow {
  research_patient_id: string;
  patient_id_hash: string;
  sex?: string | null;
  birth_year?: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface DicomSeriesRow {
  research_patient_id: string;
  study_date?: string | null;
  study_description?: string | null;
  series_instance_uid_hash: string;
  modality?: string | null;
  series_number?: number | null;
  series_description?: string | null;
  updated_at?: string;
}

export interface RtObjectRow {
  object_type: string;
  sop_instance_uid_hash: string;
  orthanc_instance_id?: string | null;
  metadata?: Record<string, unknown>;
  updated_at?: string;
}

export interface ImageArchiveRow {
  id: number;
  research_patient_id: string;
  image_role: "planning_ct" | "cbct" | "unknown_ct" | string;
  source_system: string;
  acquisition_date?: string | null;
  acquisition_time?: string | null;
  series_instance_uid_hash: string;
  frame_of_reference_uid_hash?: string | null;
  study_description?: string | null;
  series_description?: string | null;
  orthanc_instance_id?: string | null;
  instance_count?: number;
  updated_at?: string;
}

export interface MosaiqRow {
  id?: number;
  research_patient_id: string;
  [key: string]: unknown;
}

export interface ClinicalOutcome {
  id: number;
  research_patient_id: string;
  outcome_type: string;
  outcome_date?: string | null;
  outcome_value?: string | null;
  grade?: string | null;
  updated_at?: string;
}

export interface ClinicalOutcomeInput {
  research_patient_id: string;
  outcome_type: string;
  outcome_date?: string | null;
  outcome_value?: string | null;
  grade?: string | null;
}

export interface PatientResearchState {
  cohort_tag?: string | null;
  inclusion_status?: string | null;
  review_status?: string | null;
  research_note?: string | null;
}

export interface PatientDetail {
  patient: PatientRow & { metadata?: Record<string, unknown> };
  studies: Record<string, unknown>[];
  fractions: Record<string, unknown>[];
  workflows: Record<string, unknown>[];
}

export interface FractionInput {
  research_patient_id: string;
  fraction_number?: number | null;
  treatment_date?: string | null;
  machine_name?: string | null;
  delivered_mu?: number | null;
  treatment_status?: string | null;
}

export interface WorkflowInput {
  research_patient_id: string;
  workflow_step: string;
  workflow_status?: string | null;
  scheduled_date?: string | null;
  completed_date?: string | null;
}

export interface ImportValidationResult {
  ok: boolean;
  missing_files: string[];
  header_errors: Array<{ file: string; missing_columns: string[] }>;
}

export interface EtlLog {
  pipeline_name: string;
  status: string;
  message?: string | null;
  records_processed: number;
  created_at?: string;
}

export interface CommandResult {
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return fetchJson<T>(path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return fetchJson<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return fetchJson<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

export function apiDelete<T>(path: string): Promise<T> {
  return fetchJson<T>(path, { method: "DELETE" });
}
