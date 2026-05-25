import {
  Activity,
  BarChart3,
  ClipboardPlus,
  Database,
  FileHeart,
  FileInput,
  Gauge,
  HardDrive,
  Images,
  ListChecks,
  Lock,
  Pencil,
  Play,
  Plus,
  Search,
  ShieldCheck,
  Stethoscope,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  type ClinicalOutcome,
  type ClinicalOutcomeInput,
  type CollectionResponse,
  type CommandResult,
  type CohortSummary,
  type DashboardSummary,
  type DataResponse,
  type DicomSeriesRow,
  type ImagingSummary,
  type EtlLog,
  type FractionInput,
  type ImageArchiveRow,
  type ImportValidationResult,
  type MosaiqRow,
  type PatientDetail,
  type PatientRow,
  type PatientResearchState,
  type PrescriptionDistribution,
  type RtObjectRow,
  type WorkflowInput,
  apiDelete,
  apiPatch,
  apiPost,
  fetchJson,
} from "./api";
import {
  ActionButton,
  ConfirmButton,
  DataTable,
  FormRow,
  InlineAlert,
  Metric,
  Modal,
  RefreshButton,
  RowActions,
  Section,
  StateBlock,
  StatusPill,
} from "./components";
import { useAsyncData } from "./hooks";

type PageKey = "dashboard" | "statistics" | "patients" | "dicom" | "xvi" | "rt" | "mosaiq" | "outcomes" | "etl" | "security";

const navItems: Array<{ key: PageKey; label: string; icon: typeof Gauge }> = [
  { key: "dashboard", label: "总览", icon: Gauge },
  { key: "statistics", label: "统计", icon: BarChart3 },
  { key: "patients", label: "患者索引", icon: Users },
  { key: "dicom", label: "DICOM", icon: HardDrive },
  { key: "xvi", label: "XVI/CBCT", icon: Images },
  { key: "rt", label: "RT 数据", icon: FileHeart },
  { key: "mosaiq", label: "MOSAIQ", icon: ListChecks },
  { key: "outcomes", label: "结局", icon: ClipboardPlus },
  { key: "etl", label: "ETL", icon: Activity },
  { key: "security", label: "安全", icon: ShieldCheck },
];

export function App() {
  const [page, setPage] = useState<PageKey>("dashboard");
  const active = navItems.find((item) => item.key === page);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Stethoscope size={22} />
          <div>
            <strong>RT Research</strong>
            <span>Data Warehouse</span>
          </div>
        </div>
        <nav>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                className={page === item.key ? "active" : ""}
                onClick={() => setPage(item.key)}
                title={item.label}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <h1>{active?.label}</h1>
            <p>脱敏研究数据工作台</p>
          </div>
          <div className="topbar-badges">
            <span>
              <Lock size={14} />
              临床源只读
            </span>
            <span>
              <Database size={14} />
              PostgreSQL
            </span>
          </div>
        </header>
        {page === "dashboard" && <DashboardPage />}
        {page === "statistics" && <StatisticsPage />}
        {page === "patients" && <PatientsPage />}
        {page === "dicom" && <DicomPage />}
        {page === "xvi" && <XviPage />}
        {page === "rt" && <RtPage />}
        {page === "mosaiq" && <MosaiqPage />}
        {page === "outcomes" && <OutcomesPage />}
        {page === "etl" && <EtlPage />}
        {page === "security" && <SecurityPage />}
      </main>
    </div>
  );
}

function DashboardPage() {
  const loader = () => fetchJson<DataResponse<DashboardSummary>>("/dashboard/summary");
  const { data, error, loading, refetch } = useAsyncData(loader, []);
  const summary = data?.data;

  return (
    <div className="page-grid">
      <Section title="数据资产" actions={<RefreshButton onClick={refetch} loading={loading} />}>
        <StateBlock loading={loading} error={error} />
        <div className="metrics-grid">
          <Metric label="患者" value={summary?.patients ?? 0} />
          <Metric label="Study" value={summary?.studies ?? 0} />
          <Metric label="Series" value={summary?.series ?? 0} />
          <Metric label="Instance" value={summary?.instances ?? 0} />
          <Metric label="RTSTRUCT" value={summary?.rt_structures ?? 0} />
          <Metric label="RTPLAN" value={summary?.rt_plans ?? 0} />
          <Metric label="RTDOSE" value={summary?.rt_doses ?? 0} />
          <Metric label="影像归档" value={summary?.image_archives ?? 0} />
          <Metric label="分次" value={summary?.fractions ?? 0} />
        </div>
      </Section>
      <Section title="模态分布">
        <DataTable
          rows={(summary?.modalities ?? []) as Array<Record<string, unknown>>}
          columns={[
            { key: "modality", label: "Modality" },
            { key: "count", label: "数量" },
          ]}
        />
      </Section>
      <Section title="最近 ETL">
        <DataTable
          rows={(summary?.recent_etl ?? []) as unknown as Array<Record<string, unknown>>}
          columns={[
            { key: "pipeline_name", label: "Pipeline" },
            { key: "status", label: "状态", render: (row) => <StatusPill value={row.status as string} /> },
            { key: "records_processed", label: "记录" },
            { key: "created_at", label: "时间" },
          ]}
        />
      </Section>
    </div>
  );
}

function StatisticsPage() {
  const cohort = useAsyncData(() => fetchJson<DataResponse<CohortSummary>>("/statistics/cohort-summary"), []);
  const prescriptions = useAsyncData(
    () => fetchJson<DataResponse<PrescriptionDistribution>>("/statistics/prescription-distribution"),
    [],
  );
  const imaging = useAsyncData(() => fetchJson<DataResponse<ImagingSummary>>("/statistics/imaging-summary"), []);
  const cohortData = cohort.data?.data;
  const prescriptionData = prescriptions.data?.data;
  const imagingData = imaging.data?.data;
  const busy = cohort.loading || prescriptions.loading || imaging.loading;

  function refreshAll() {
    void cohort.refetch();
    void prescriptions.refetch();
    void imaging.refetch();
  }

  function exportPatientsCsv() {
    window.location.href = "/api/v1/export/patients-csv";
  }

  return (
    <div className="page-grid">
      <Section
        title="队列概览"
        actions={
          <div className="toolbar">
            <ActionButton onClick={exportPatientsCsv}>
              <FileInput size={15} />
              导出患者 CSV
            </ActionButton>
            <RefreshButton onClick={refreshAll} loading={busy} />
          </div>
        }
      >
        <StateBlock loading={cohort.loading} error={cohort.error} />
        <div className="metrics-grid">
          <Metric label="患者总数" value={cohortData?.patient_count ?? 0} />
          <Metric label="年龄中位数" value={formatSummaryValue(cohortData?.age_summary.median)} />
          <Metric label="分次数中位数" value={formatSummaryValue(cohortData?.fraction_summary.median)} />
          <Metric label="CBCT 中位数" value={formatSummaryValue(cohortData?.cbct_summary.median)} />
          <Metric label="计划 CT 中位数" value={formatSummaryValue(cohortData?.planning_ct_summary.median)} />
        </div>
      </Section>

      <Section title="患者基础分布">
        <DataTable
          rows={[
            ...(cohortData?.sex_distribution ?? []).map((row) => ({ group: "性别", ...row })),
            ...(cohortData?.research_states.cohort_tags ?? []).map((row) => ({ group: "队列标签", ...row })),
            ...(cohortData?.research_states.inclusion_status ?? []).map((row) => ({ group: "入组状态", ...row })),
            ...(cohortData?.research_states.review_status ?? []).map((row) => ({ group: "审核状态", ...row })),
          ]}
          columns={[
            { key: "group", label: "分组" },
            { key: "label", label: "取值" },
            { key: "count", label: "数量" },
          ]}
        />
      </Section>

      <Section title="处方与治疗分布">
        <DataTable
          rows={(prescriptionData?.prescription_schemes ?? []) as Array<Record<string, unknown>>}
          columns={[
            { key: "treatment_site", label: "部位" },
            { key: "technique", label: "技术" },
            { key: "prescription_dose_gy", label: "总剂量 Gy" },
            { key: "fractions", label: "分次数" },
            { key: "patient_count", label: "患者数" },
          ]}
        />
      </Section>

      <Section title="技术、设备与影像">
        <div className="split-grid">
          <DataTable
            rows={[
              ...(prescriptionData?.techniques ?? []).map((row) => ({ group: "技术", ...row })),
              ...(prescriptionData?.treatment_sites ?? []).map((row) => ({ group: "部位", ...row })),
              ...(imagingData?.by_role ?? []).map((row) => ({ group: "影像角色", ...row })),
              ...(imagingData?.by_source ?? []).map((row) => ({ group: "来源系统", ...row })),
            ]}
            columns={[
              { key: "group", label: "分组" },
              { key: "label", label: "取值" },
              { key: "count", label: "数量" },
            ]}
          />
          <DataTable
            rows={(prescriptionData?.machines ?? []) as Array<Record<string, unknown>>}
            columns={[
              { key: "machine_name", label: "设备" },
              { key: "fraction_count", label: "分次数" },
              { key: "patient_count", label: "患者数" },
            ]}
          />
        </div>
      </Section>

      <Section title="患者影像归档概览">
        <DataTable
          rows={(imagingData?.per_patient ?? []) as Array<Record<string, unknown>>}
          columns={[
            { key: "research_patient_id", label: "研究 ID" },
            { key: "planning_ct_count", label: "计划 CT" },
            { key: "cbct_count", label: "CBCT" },
            { key: "unknown_ct_count", label: "未知 CT" },
            { key: "latest_acquisition_date", label: "最近采集日期" },
          ]}
        />
      </Section>
    </div>
  );
}

function formatSummaryValue(value?: number | null) {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(1).replace(/\.0$/, "");
}

function PatientsPage() {
  const [query, setQuery] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<string | null>(null);
  const [statePatient, setStatePatient] = useState<PatientRow | null>(null);
  const [outcomePatient, setOutcomePatient] = useState<PatientRow | null>(null);
  const [researchState, setResearchState] = useState<PatientResearchState>({});
  const [outcomeDraft, setOutcomeDraft] = useState<ClinicalOutcomeInput>({ research_patient_id: "", outcome_type: "" });
  const [notice, setNotice] = useState<string | null>(null);
  const path = useMemo(() => `/patients?limit=50&offset=0${query ? `&q=${encodeURIComponent(query)}` : ""}`, [query]);
  const { data, error, loading, refetch } = useAsyncData(() => fetchJson<CollectionResponse<PatientRow>>(path), [path]);
  const detail = useAsyncData(
    () =>
      selectedPatient
        ? fetchJson<DataResponse<PatientDetail>>(`/patients/${encodeURIComponent(selectedPatient)}`)
        : Promise.resolve({ data: null as unknown as PatientDetail }),
    [selectedPatient],
  );

  async function saveResearchState() {
    if (!statePatient) return;
    await apiPatch<DataResponse<Record<string, unknown>>>(
      `/patients/${encodeURIComponent(statePatient.research_patient_id)}/research-state`,
      researchState,
    );
    setStatePatient(null);
    setNotice("研究状态已更新");
    await refetch();
  }

  async function savePatientOutcome() {
    await apiPost<DataResponse<ClinicalOutcome>>("/outcomes", outcomeDraft);
    setOutcomePatient(null);
    setNotice("临床结局已新增");
  }

  return (
    <>
      <Section
        title="患者研究队列"
        actions={
          <div className="toolbar">
            <label className="search-box">
              <Search size={16} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="research_patient_id" />
            </label>
            <RefreshButton onClick={refetch} loading={loading} />
          </div>
        }
      >
        {notice ? <InlineAlert tone="success">{notice}</InlineAlert> : null}
        <StateBlock loading={loading} error={error} />
        <DataTable
          rows={(data?.data ?? []) as unknown as Array<Record<string, unknown>>}
          columns={[
            { key: "research_patient_id", label: "研究 ID" },
            { key: "patient_id_hash", label: "PatientID Hash" },
            { key: "sex", label: "性别" },
            { key: "birth_year", label: "出生年" },
            { key: "updated_at", label: "更新时间" },
            {
              key: "actions",
              label: "操作",
              render: (row) => {
                const patient = row as unknown as PatientRow;
                return (
                  <RowActions>
                    <button className="icon-button" title="详情" onClick={() => setSelectedPatient(patient.research_patient_id)}>
                      <Search size={15} />
                    </button>
                    <button
                      className="icon-button"
                      title="编辑研究状态"
                      onClick={() => {
                        setResearchState({});
                        setStatePatient(patient);
                      }}
                    >
                      <Pencil size={15} />
                    </button>
                    <button
                      className="icon-button"
                      title="新增结局"
                      onClick={() => {
                        setOutcomeDraft({ research_patient_id: patient.research_patient_id, outcome_type: "" });
                        setOutcomePatient(patient);
                      }}
                    >
                      <Plus size={15} />
                    </button>
                  </RowActions>
                );
              },
            },
          ]}
        />
      </Section>

      <Modal title="患者详情" open={selectedPatient !== null} onClose={() => setSelectedPatient(null)}>
        <StateBlock loading={detail.loading} error={detail.error} />
        {detail.data?.data ? (
          <div className="detail-grid">
            <InlineAlert>该详情仅显示脱敏研究 ID、hash 和研究侧记录。</InlineAlert>
            <DataTable
              rows={[detail.data.data.patient as unknown as Record<string, unknown>]}
              columns={[
                { key: "research_patient_id", label: "研究 ID" },
                { key: "patient_id_hash", label: "PatientID Hash" },
                { key: "sex", label: "性别" },
                { key: "birth_year", label: "出生年" },
              ]}
            />
            <h3>Study</h3>
            <DataTable
              rows={detail.data.data.studies}
              columns={[
                { key: "study_date", label: "日期" },
                { key: "study_description", label: "描述" },
                { key: "study_instance_uid_hash", label: "Study UID Hash" },
              ]}
            />
            <h3>分次</h3>
            <DataTable rows={detail.data.data.fractions} columns={fractionColumns} />
            <h3>流程</h3>
            <DataTable rows={detail.data.data.workflows} columns={workflowColumns} />
          </div>
        ) : null}
      </Modal>

      <Modal title="编辑研究状态" open={statePatient !== null} onClose={() => setStatePatient(null)}>
        <div className="form-grid">
          <InlineAlert>仅记录研究队列状态，不修改临床系统。</InlineAlert>
          <FormRow label="队列标签">
            <input value={researchState.cohort_tag ?? ""} onChange={(event) => setResearchState({ ...researchState, cohort_tag: event.target.value })} />
          </FormRow>
          <FormRow label="纳入状态">
            <select value={researchState.inclusion_status ?? ""} onChange={(event) => setResearchState({ ...researchState, inclusion_status: event.target.value })}>
              <option value="">未设置</option>
              <option value="included">纳入</option>
              <option value="excluded">排除</option>
              <option value="pending">待定</option>
            </select>
          </FormRow>
          <FormRow label="审核状态">
            <select value={researchState.review_status ?? ""} onChange={(event) => setResearchState({ ...researchState, review_status: event.target.value })}>
              <option value="">未设置</option>
              <option value="needs_review">待审核</option>
              <option value="reviewed">已审核</option>
            </select>
          </FormRow>
          <FormRow label="研究备注">
            <textarea value={researchState.research_note ?? ""} onChange={(event) => setResearchState({ ...researchState, research_note: event.target.value })} />
          </FormRow>
          <div className="form-actions">
            <ActionButton onClick={() => void saveResearchState()}>保存</ActionButton>
          </div>
        </div>
      </Modal>

      <OutcomeFormModal
        title="新增临床结局"
        open={outcomePatient !== null}
        draft={outcomeDraft}
        onChange={setOutcomeDraft}
        onClose={() => setOutcomePatient(null)}
        onSubmit={() => void savePatientOutcome()}
      />
    </>
  );
}

function DicomPage() {
  const [modality, setModality] = useState("");
  const path = `/dicom/series?limit=80&offset=0${modality ? `&modality=${encodeURIComponent(modality)}` : ""}`;
  const { data, error, loading, refetch } = useAsyncData(() => fetchJson<CollectionResponse<DicomSeriesRow>>(path), [path]);

  return (
    <Section
      title="DICOM Series 浏览"
      actions={
        <div className="toolbar">
          <select value={modality} onChange={(event) => setModality(event.target.value)}>
            <option value="">全部模态</option>
            <option value="CT">CT</option>
            <option value="RTSTRUCT">RTSTRUCT</option>
            <option value="RTPLAN">RTPLAN</option>
            <option value="RTDOSE">RTDOSE</option>
            <option value="REG">REG</option>
          </select>
          <RefreshButton onClick={refetch} loading={loading} />
        </div>
      }
    >
      <StateBlock loading={loading} error={error} />
      <DataTable
        rows={(data?.data ?? []) as unknown as Array<Record<string, unknown>>}
        columns={[
          { key: "research_patient_id", label: "研究 ID" },
          { key: "study_date", label: "Study Date" },
          { key: "modality", label: "模态" },
          { key: "series_description", label: "Series Description" },
          { key: "series_instance_uid_hash", label: "Series UID Hash" },
        ]}
      />
    </Section>
  );
}

function XviPage() {
  const [patientId, setPatientId] = useState("");
  const [imageRole, setImageRole] = useState("");
  const path = useMemo(() => {
    const params = new URLSearchParams({ limit: "100", offset: "0" });
    if (patientId) params.set("research_patient_id", patientId);
    if (imageRole) params.set("image_role", imageRole);
    return `/xvi/image-archive?${params.toString()}`;
  }, [patientId, imageRole]);
  const { data, error, loading, refetch } = useAsyncData(() => fetchJson<CollectionResponse<ImageArchiveRow>>(path), [path]);

  return (
    <Section
      title="XVI / CBCT 影像归档"
      actions={
        <div className="toolbar">
          <label className="search-box">
            <Search size={16} />
            <input value={patientId} onChange={(event) => setPatientId(event.target.value)} placeholder="research_patient_id" />
          </label>
          <select value={imageRole} onChange={(event) => setImageRole(event.target.value)}>
            <option value="">全部影像</option>
            <option value="planning_ct">计划 CT</option>
            <option value="cbct">XVI CBCT</option>
            <option value="unknown_ct">未分类 CT</option>
          </select>
          <RefreshButton onClick={refetch} loading={loading} />
        </div>
      }
    >
      <InlineAlert>归档记录按 DICOM Series 去重；原始图像仍由 Orthanc 存储，本页只展示脱敏索引。</InlineAlert>
      <StateBlock loading={loading} error={error} />
      <DataTable
        rows={(data?.data ?? []) as unknown as Array<Record<string, unknown>>}
        columns={[
          { key: "research_patient_id", label: "研究 ID" },
          { key: "image_role", label: "影像类型", render: (row) => imageRoleLabel(row.image_role as string) },
          { key: "source_system", label: "来源" },
          { key: "acquisition_date", label: "采集日期" },
          { key: "acquisition_time", label: "采集时间" },
          { key: "instance_count", label: "切片数" },
          { key: "series_description", label: "Series Description" },
          { key: "series_instance_uid_hash", label: "Series UID Hash" },
          { key: "frame_of_reference_uid_hash", label: "Frame Hash" },
        ]}
      />
    </Section>
  );
}

function imageRoleLabel(value?: string | null) {
  if (value === "planning_ct") return "计划 CT";
  if (value === "cbct") return "XVI CBCT";
  if (value === "unknown_ct") return "未分类 CT";
  return value ?? "-";
}

function RtPage() {
  const objects = useAsyncData(() => fetchJson<CollectionResponse<RtObjectRow>>("/rt/objects?limit=80&offset=0"), []);
  const dvh = useAsyncData(() => fetchJson<CollectionResponse<Record<string, unknown>>>("/rt/dvh-metrics?limit=80&offset=0"), []);

  return (
    <div className="page-grid">
      <Section title="RT 对象" actions={<RefreshButton onClick={objects.refetch} loading={objects.loading} />}>
        <StateBlock loading={objects.loading} error={objects.error} />
        <DataTable
          rows={(objects.data?.data ?? []) as unknown as Array<Record<string, unknown>>}
          columns={[
            { key: "object_type", label: "类型" },
            { key: "sop_instance_uid_hash", label: "SOP UID Hash" },
            { key: "orthanc_instance_id", label: "Orthanc ID" },
            { key: "updated_at", label: "更新时间" },
          ]}
        />
      </Section>
      <Section title="DVH 指标" actions={<RefreshButton onClick={dvh.refetch} loading={dvh.loading} />}>
        <StateBlock loading={dvh.loading} error={dvh.error} />
        <DataTable
          rows={dvh.data?.data ?? []}
          columns={[
            { key: "research_patient_id", label: "研究 ID" },
            { key: "roi_name", label: "ROI" },
            { key: "metric_name", label: "指标" },
            { key: "metric_value", label: "值" },
            { key: "metric_unit", label: "单位" },
          ]}
        />
      </Section>
    </div>
  );
}

function MosaiqPage() {
  const prescriptions = useAsyncData(() => fetchJson<CollectionResponse<MosaiqRow>>("/mosaiq/prescriptions?limit=50"), []);
  const fractions = useAsyncData(() => fetchJson<CollectionResponse<MosaiqRow>>("/mosaiq/fractions?limit=50"), []);
  const workflows = useAsyncData(() => fetchJson<CollectionResponse<MosaiqRow>>("/mosaiq/workflows?limit=50"), []);
  const [importResult, setImportResult] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [fractionModal, setFractionModal] = useState<{ id?: number; draft: FractionInput } | null>(null);
  const [workflowModal, setWorkflowModal] = useState<{ id?: number; draft: WorkflowInput } | null>(null);

  async function validateCsv() {
    setRunning(true);
    try {
      const response = await apiPost<DataResponse<ImportValidationResult>>("/imports/mosaiq/validate");
      setImportResult(JSON.stringify(response.data, null, 2));
    } finally {
      setRunning(false);
    }
  }

  async function runImport() {
    setRunning(true);
    try {
      const response = await apiPost<DataResponse<CommandResult>>("/imports/mosaiq/run");
      setImportResult(JSON.stringify(response.data, null, 2));
      await Promise.all([prescriptions.refetch(), fractions.refetch(), workflows.refetch()]);
    } finally {
      setRunning(false);
    }
  }

  async function saveFraction() {
    if (!fractionModal) return;
    if (fractionModal.id) {
      await apiPatch<DataResponse<MosaiqRow>>(`/mosaiq/fractions/${fractionModal.id}`, fractionModal.draft);
    } else {
      await apiPost<DataResponse<MosaiqRow>>("/mosaiq/fractions", fractionModal.draft);
    }
    setFractionModal(null);
    await fractions.refetch();
  }

  async function saveWorkflow() {
    if (!workflowModal) return;
    if (workflowModal.id) {
      await apiPatch<DataResponse<MosaiqRow>>(`/mosaiq/workflows/${workflowModal.id}`, workflowModal.draft);
    } else {
      await apiPost<DataResponse<MosaiqRow>>("/mosaiq/workflows", workflowModal.draft);
    }
    setWorkflowModal(null);
    await workflows.refetch();
  }

  async function deleteFraction(id?: number) {
    if (!id) return;
    await apiDelete<DataResponse<{ deleted: boolean }>>(`/mosaiq/fractions/${id}`);
    await fractions.refetch();
  }

  async function deleteWorkflow(id?: number) {
    if (!id) return;
    await apiDelete<DataResponse<{ deleted: boolean }>>(`/mosaiq/workflows/${id}`);
    await workflows.refetch();
  }

  return (
    <div className="page-grid">
      <Section
        title="CSV 导入中心"
        actions={
          <div className="toolbar">
            <ActionButton onClick={() => void validateCsv()} disabled={running}>
              <FileInput size={15} />
              校验 CSV
            </ActionButton>
            <ActionButton onClick={() => void runImport()} disabled={running}>
              <Play size={15} />
              导入 CSV
            </ActionButton>
          </div>
        }
      >
        <InlineAlert>导入前请确认 CSV 已移除姓名、身份证、电话、住址和可识别自由文本。</InlineAlert>
        {importResult ? <pre className="command-output">{importResult}</pre> : <div className="state">使用 data_templates 中的 MOSAIQ CSV 模板进行校验和导入。</div>}
      </Section>
      <Section title="处方">
        <StateBlock loading={prescriptions.loading} error={prescriptions.error} />
        <DataTable rows={(prescriptions.data?.data ?? []) as Array<Record<string, unknown>>} columns={mosaiqColumns} />
      </Section>
      <Section
        title="分次治疗"
        actions={
          <ActionButton onClick={() => setFractionModal({ draft: { research_patient_id: "" } })}>
            <Plus size={15} />
            新增分次
          </ActionButton>
        }
      >
        <StateBlock loading={fractions.loading} error={fractions.error} />
        <DataTable
          rows={(fractions.data?.data ?? []) as Array<Record<string, unknown>>}
          columns={[
            ...fractionColumns,
            {
              key: "actions",
              label: "操作",
              render: (row) => {
                const fraction = row as unknown as MosaiqRow;
                return (
                  <RowActions>
                    <button
                      className="icon-button"
                      title="编辑"
                      onClick={() =>
                        setFractionModal({
                          id: fraction.id,
                          draft: {
                            research_patient_id: String(fraction.research_patient_id ?? ""),
                            fraction_number: fraction.fraction_number as number | null,
                            treatment_date: fraction.treatment_date as string | null,
                            machine_name: fraction.machine_name as string | null,
                            delivered_mu: fraction.delivered_mu as number | null,
                            treatment_status: fraction.treatment_status as string | null,
                          },
                        })
                      }
                    >
                      <Pencil size={15} />
                    </button>
                    <ConfirmButton onConfirm={() => void deleteFraction(fraction.id)} />
                  </RowActions>
                );
              },
            },
          ]}
        />
      </Section>
      <Section
        title="流程状态"
        actions={
          <ActionButton onClick={() => setWorkflowModal({ draft: { research_patient_id: "", workflow_step: "" } })}>
            <Plus size={15} />
            新增流程
          </ActionButton>
        }
      >
        <StateBlock loading={workflows.loading} error={workflows.error} />
        <DataTable
          rows={(workflows.data?.data ?? []) as Array<Record<string, unknown>>}
          columns={[
            ...workflowColumns,
            {
              key: "actions",
              label: "操作",
              render: (row) => {
                const workflow = row as unknown as MosaiqRow;
                return (
                  <RowActions>
                    <button
                      className="icon-button"
                      title="编辑"
                      onClick={() =>
                        setWorkflowModal({
                          id: workflow.id,
                          draft: {
                            research_patient_id: String(workflow.research_patient_id ?? ""),
                            workflow_step: String(workflow.workflow_step ?? ""),
                            workflow_status: workflow.workflow_status as string | null,
                            scheduled_date: workflow.scheduled_date as string | null,
                            completed_date: workflow.completed_date as string | null,
                          },
                        })
                      }
                    >
                      <Pencil size={15} />
                    </button>
                    <ConfirmButton onConfirm={() => void deleteWorkflow(workflow.id)} />
                  </RowActions>
                );
              },
            },
          ]}
        />
      </Section>
      <FractionFormModal
        open={fractionModal !== null}
        draft={fractionModal?.draft ?? { research_patient_id: "" }}
        onChange={(draft) => setFractionModal(fractionModal ? { ...fractionModal, draft } : { draft })}
        onClose={() => setFractionModal(null)}
        onSubmit={() => void saveFraction()}
      />
      <WorkflowFormModal
        open={workflowModal !== null}
        draft={workflowModal?.draft ?? { research_patient_id: "", workflow_step: "" }}
        onChange={(draft) => setWorkflowModal(workflowModal ? { ...workflowModal, draft } : { draft })}
        onClose={() => setWorkflowModal(null)}
        onSubmit={() => void saveWorkflow()}
      />
    </div>
  );
}

const mosaiqColumns = [
  { key: "research_patient_id", label: "研究 ID" },
  { key: "prescription_dose_gy", label: "处方 Gy" },
  { key: "fractions", label: "分次数" },
  { key: "dose_per_fraction_gy", label: "单次 Gy" },
  { key: "technique", label: "技术" },
];

const fractionColumns = [
  { key: "research_patient_id", label: "研究 ID" },
  { key: "fraction_number", label: "分次" },
  { key: "treatment_date", label: "日期" },
  { key: "machine_name", label: "机器" },
  { key: "treatment_status", label: "状态" },
];

const workflowColumns = [
  { key: "research_patient_id", label: "研究 ID" },
  { key: "workflow_step", label: "步骤" },
  { key: "workflow_status", label: "状态" },
  { key: "scheduled_date", label: "计划日期" },
  { key: "completed_date", label: "完成日期" },
];

function OutcomesPage() {
  const outcomes = useAsyncData(() => fetchJson<CollectionResponse<ClinicalOutcome>>("/outcomes?limit=80&offset=0"), []);
  const [draft, setDraft] = useState<ClinicalOutcomeInput>({ research_patient_id: "", outcome_type: "" });
  const [editing, setEditing] = useState<ClinicalOutcome | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  function openCreate() {
    setEditing(null);
    setDraft({ research_patient_id: "", outcome_type: "" });
    setModalOpen(true);
  }

  function openEdit(outcome: ClinicalOutcome) {
    setEditing(outcome);
    setDraft({
      research_patient_id: outcome.research_patient_id,
      outcome_type: outcome.outcome_type,
      outcome_date: outcome.outcome_date,
      outcome_value: outcome.outcome_value,
      grade: outcome.grade,
    });
    setModalOpen(true);
  }

  async function saveOutcome() {
    if (editing) {
      await apiPatch<DataResponse<ClinicalOutcome>>(`/outcomes/${editing.id}`, draft);
      setNotice("临床结局已更新");
    } else {
      await apiPost<DataResponse<ClinicalOutcome>>("/outcomes", draft);
      setNotice("临床结局已新增");
    }
    setModalOpen(false);
    await outcomes.refetch();
  }

  async function deleteOutcome(id: number) {
    await apiDelete<DataResponse<{ deleted: boolean }>>(`/outcomes/${id}`);
    setNotice("临床结局已删除");
    await outcomes.refetch();
  }

  return (
    <>
      <Section
        title="临床结局管理"
        actions={
          <div className="toolbar">
            <ActionButton onClick={openCreate}>
              <Plus size={15} />
              新增结局
            </ActionButton>
            <RefreshButton onClick={outcomes.refetch} loading={outcomes.loading} />
          </div>
        }
      >
        <InlineAlert>本页仅维护研究侧结局数据，不写回临床系统。</InlineAlert>
        {notice ? <InlineAlert tone="success">{notice}</InlineAlert> : null}
        <StateBlock loading={outcomes.loading} error={outcomes.error} />
        <DataTable
          rows={(outcomes.data?.data ?? []) as unknown as Array<Record<string, unknown>>}
          columns={[
            { key: "research_patient_id", label: "研究 ID" },
            { key: "outcome_type", label: "结局类型" },
            { key: "outcome_date", label: "日期" },
            { key: "outcome_value", label: "值" },
            { key: "grade", label: "等级" },
            { key: "updated_at", label: "更新时间" },
            {
              key: "actions",
              label: "操作",
              render: (row) => {
                const outcome = row as unknown as ClinicalOutcome;
                return (
                  <RowActions>
                    <button className="icon-button" title="编辑" onClick={() => openEdit(outcome)}>
                      <Pencil size={15} />
                    </button>
                    <ConfirmButton onConfirm={() => void deleteOutcome(outcome.id)} />
                  </RowActions>
                );
              },
            },
          ]}
        />
      </Section>
      <OutcomeFormModal
        title={editing ? "编辑临床结局" : "新增临床结局"}
        open={modalOpen}
        draft={draft}
        onChange={setDraft}
        onClose={() => setModalOpen(false)}
        onSubmit={() => void saveOutcome()}
      />
    </>
  );
}

function OutcomeFormModal({
  title,
  open,
  draft,
  onChange,
  onClose,
  onSubmit,
}: {
  title: string;
  open: boolean;
  draft: ClinicalOutcomeInput;
  onChange: (draft: ClinicalOutcomeInput) => void;
  onClose: () => void;
  onSubmit: () => void;
}) {
  return (
    <Modal title={title} open={open} onClose={onClose}>
      <div className="form-grid">
        <InlineAlert>不要在结局值或备注中输入姓名、身份证、电话、住址等直接身份信息。</InlineAlert>
        <FormRow label="研究 ID">
          <input value={draft.research_patient_id} onChange={(event) => onChange({ ...draft, research_patient_id: event.target.value })} />
        </FormRow>
        <FormRow label="结局类型">
          <input value={draft.outcome_type} onChange={(event) => onChange({ ...draft, outcome_type: event.target.value })} />
        </FormRow>
        <FormRow label="结局日期">
          <input type="date" value={draft.outcome_date ?? ""} onChange={(event) => onChange({ ...draft, outcome_date: event.target.value || null })} />
        </FormRow>
        <FormRow label="结局值">
          <input value={draft.outcome_value ?? ""} onChange={(event) => onChange({ ...draft, outcome_value: event.target.value })} />
        </FormRow>
        <FormRow label="等级">
          <input value={draft.grade ?? ""} onChange={(event) => onChange({ ...draft, grade: event.target.value })} />
        </FormRow>
        <div className="form-actions">
          <ActionButton onClick={onSubmit}>保存</ActionButton>
        </div>
      </div>
    </Modal>
  );
}

function FractionFormModal({
  open,
  draft,
  onChange,
  onClose,
  onSubmit,
}: {
  open: boolean;
  draft: FractionInput;
  onChange: (draft: FractionInput) => void;
  onClose: () => void;
  onSubmit: () => void;
}) {
  return (
    <Modal title="分次治疗记录" open={open} onClose={onClose}>
      <div className="form-grid">
        <InlineAlert>这里维护研究侧治疗分次记录，不修改 MOSAIQ。</InlineAlert>
        <FormRow label="研究 ID">
          <input value={draft.research_patient_id} onChange={(event) => onChange({ ...draft, research_patient_id: event.target.value })} />
        </FormRow>
        <FormRow label="分次数">
          <input type="number" value={draft.fraction_number ?? ""} onChange={(event) => onChange({ ...draft, fraction_number: event.target.value ? Number(event.target.value) : null })} />
        </FormRow>
        <FormRow label="治疗日期">
          <input type="date" value={draft.treatment_date ?? ""} onChange={(event) => onChange({ ...draft, treatment_date: event.target.value || null })} />
        </FormRow>
        <FormRow label="机器">
          <input value={draft.machine_name ?? ""} onChange={(event) => onChange({ ...draft, machine_name: event.target.value || null })} />
        </FormRow>
        <FormRow label="MU">
          <input type="number" step="0.01" value={draft.delivered_mu ?? ""} onChange={(event) => onChange({ ...draft, delivered_mu: event.target.value ? Number(event.target.value) : null })} />
        </FormRow>
        <FormRow label="状态">
          <input value={draft.treatment_status ?? ""} onChange={(event) => onChange({ ...draft, treatment_status: event.target.value || null })} />
        </FormRow>
        <div className="form-actions">
          <ActionButton onClick={onSubmit}>保存</ActionButton>
        </div>
      </div>
    </Modal>
  );
}

function WorkflowFormModal({
  open,
  draft,
  onChange,
  onClose,
  onSubmit,
}: {
  open: boolean;
  draft: WorkflowInput;
  onChange: (draft: WorkflowInput) => void;
  onClose: () => void;
  onSubmit: () => void;
}) {
  return (
    <Modal title="流程状态记录" open={open} onClose={onClose}>
      <div className="form-grid">
        <InlineAlert>这里维护研究侧流程状态记录，不修改 MOSAIQ。</InlineAlert>
        <FormRow label="研究 ID">
          <input value={draft.research_patient_id} onChange={(event) => onChange({ ...draft, research_patient_id: event.target.value })} />
        </FormRow>
        <FormRow label="流程步骤">
          <input value={draft.workflow_step} onChange={(event) => onChange({ ...draft, workflow_step: event.target.value })} />
        </FormRow>
        <FormRow label="状态">
          <input value={draft.workflow_status ?? ""} onChange={(event) => onChange({ ...draft, workflow_status: event.target.value || null })} />
        </FormRow>
        <FormRow label="计划日期">
          <input type="date" value={draft.scheduled_date ?? ""} onChange={(event) => onChange({ ...draft, scheduled_date: event.target.value || null })} />
        </FormRow>
        <FormRow label="完成日期">
          <input type="date" value={draft.completed_date ?? ""} onChange={(event) => onChange({ ...draft, completed_date: event.target.value || null })} />
        </FormRow>
        <div className="form-actions">
          <ActionButton onClick={onSubmit}>保存</ActionButton>
        </div>
      </div>
    </Modal>
  );
}

function EtlPage() {
  const [result, setResult] = useState<CommandResult | null>(null);
  const logs = useAsyncData(() => fetchJson<CollectionResponse<EtlLog>>("/etl/logs?limit=50"), []);
  const [running, setRunning] = useState<string | null>(null);

  async function runCommand(path: string, name: string) {
    setRunning(name);
    setResult(null);
    try {
      const response = await fetchJson<DataResponse<CommandResult>>(path, { method: "POST" });
      setResult(response.data);
      await logs.refetch();
    } finally {
      setRunning(null);
    }
  }

  return (
    <div className="page-grid">
      <Section
        title="ETL 控制台"
        actions={
          <div className="toolbar">
            <button onClick={() => void runCommand("/etl/run-orthanc", "orthanc")} disabled={running !== null}>
              <Play size={15} />
              Orthanc ETL
            </button>
            <button onClick={() => void runCommand("/etl/import-mosaiq", "mosaiq")} disabled={running !== null}>
              <Play size={15} />
              MOSAIQ CSV
            </button>
          </div>
        }
      >
        {running ? <div className="state">正在运行 {running}</div> : null}
        {result ? <pre className="command-output">{JSON.stringify(result, null, 2)}</pre> : <div className="state">选择一个任务运行</div>}
      </Section>
      <Section title="ETL 日志" actions={<RefreshButton onClick={logs.refetch} loading={logs.loading} />}>
        <StateBlock loading={logs.loading} error={logs.error} />
        <DataTable
          rows={(logs.data?.data ?? []) as unknown as Array<Record<string, unknown>>}
          columns={[
            { key: "pipeline_name", label: "Pipeline" },
            { key: "status", label: "状态", render: (row) => <StatusPill value={row.status as string} /> },
            { key: "records_processed", label: "记录" },
            { key: "message", label: "消息" },
            { key: "created_at", label: "时间" },
          ]}
        />
      </Section>
    </div>
  );
}

function SecurityPage() {
  return (
    <div className="page-grid">
      <Section title="脱敏边界">
        <div className="security-grid">
          <Metric label="PatientID" value="Salted Hash" />
          <Metric label="UID" value="Salted Hash" />
          <Metric label="患者姓名" value="不入库" />
          <Metric label="写回临床系统" value="禁止" />
        </div>
      </Section>
      <Section title="操作原则">
        <ul className="check-list">
          <li>界面只展示 research_patient_id 和 hash 字段。</li>
          <li>ETL 从 Orthanc 与 CSV 读取研究副本，不修改临床系统。</li>
          <li>CSV 导入前应移除姓名、身份证、电话、住址和可识别自由文本。</li>
          <li>生产环境应增加登录、角色权限、审计日志和 HTTPS。</li>
        </ul>
      </Section>
    </div>
  );
}
