# v0.2.0 研究统计与导出模块技术设计

## 目标

v0.2.0 增加一个可立即用于现有研究仓库数据的统计模块，聚焦队列概览、处方/治疗分布、影像归档统计和患者级 CSV 导出。

该版本不实现生存分析、摆位误差模型、计划质量 HI/CI 或 DVH 高级统计；这些能力依赖更稳定的数据字典和解析流程，应放入后续版本。

## 范围

### 后端 API

新增 `api/app/routers/statistics.py`：

- `GET /api/v1/statistics/cohort-summary`
- `GET /api/v1/statistics/prescription-distribution`
- `GET /api/v1/statistics/imaging-summary`

新增 `api/app/routers/export.py`：

- `GET /api/v1/export/patients-csv`

所有接口只返回脱敏字段，不返回患者姓名、身份证、电话、住址、原始 PatientID 或原始 UID。

### 前端

新增 `统计` 页面，使用现有指标卡和表格组件展示：

- 队列总览。
- 性别分布。
- 近似年龄摘要。
- 处方方案分布。
- 治疗部位、技术、机器使用统计。
- 计划 CT / CBCT / 未分类 CT 影像归档统计。
- 患者级 CSV 导出按钮。

图表库暂不作为必需依赖。后续如需要饼图、柱状图，再引入 `recharts`。

## 数据来源

- `patient_index`
- `patient_index.metadata->'research_state'`
- `mosaiq_prescription`
- `treatment_fraction`
- `image_archive`

## 统计定义

### 队列概览

- `patient_count`：`patient_index` 总数。
- `sex_distribution`：按 `sex` 分组。
- `age_summary`：以当前年份减 `birth_year` 得到近似年龄，返回 `min`、`p25`、`median`、`p75`、`max`。
- `research_state_distribution`：从 `metadata.research_state` 提取 `cohort_tag`、`inclusion_status`、`review_status` 分布。
- `fraction_summary`：每患者治疗分次数的 `min`、`p25`、`median`、`p75`、`max`。
- `cbct_summary`：每患者 CBCT 次数的 `min`、`p25`、`median`、`p75`、`max`。
- `planning_ct_summary`：每患者计划 CT 次数的 `min`、`p25`、`median`、`p75`、`max`。

### 处方与治疗分布

- `prescription_schemes`：按 `prescription_dose_gy`、`fractions`、`dose_per_fraction_gy` 分组，按患者去重。
- `techniques`：按 `technique` 分组。
- `treatment_sites`：按 `treatment_site` 分组。
- `machines`：按 `machine_name` 分组，统计分次数和患者数。

### 影像统计

- `by_role`：按 `image_role` 分组。
- `by_source`：按 `source_system` 分组。
- `per_patient`：每患者计划 CT、CBCT、未分类 CT 数量。

## CSV 导出

`GET /api/v1/export/patients-csv` 返回 UTF-8 CSV。列包括：

- `research_patient_id`
- `sex`
- `birth_year`
- `cohort_tag`
- `inclusion_status`
- `review_status`
- `treatment_site`
- `technique`
- `prescription_dose_gy`
- `fractions`
- `dose_per_fraction_gy`
- `fraction_count`
- `planning_ct_count`
- `cbct_count`
- `unknown_ct_count`

## 安全要求

- 不返回原始 PatientID。
- 不返回患者姓名、身份证、电话、住址。
- 不返回原始 StudyInstanceUID、SeriesInstanceUID、SOPInstanceUID。
- 导出 CSV 仅用于研究副本，生产部署应增加登录、权限和审计。

## 后续版本

- v0.3：XVI couch shift 解析、摆位误差统计、更多 CSV 导出。
- v0.4：DVH 高级聚合、计划质量指标、生存分析数据字典。
- v0.5：生存分析和预测模型。
