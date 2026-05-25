# 放疗研究统计模块实现 Prompt

## 背景

当前 `rt-research` 项目已经具备：

- Orthanc DICOM 接收和存储。
- PostgreSQL 研究数据库。
- Python ETL 脱敏入库。
- Monaco 计划 CT、RTSTRUCT、RTPLAN、RTDOSE 解析。
- XVI/CBCT 影像归档。
- MOSAIQ CSV 导入。
- React Web 工作台。

下一版统计模块应优先服务“已有数据可立即统计”的场景，不提前实现依赖缺失数据的高级分析。

## v0.2.0 范围

### 后端

新增：

- `api/app/routers/statistics.py`
- `api/app/routers/export.py`

接口：

- `GET /api/v1/statistics/cohort-summary`
- `GET /api/v1/statistics/prescription-distribution`
- `GET /api/v1/statistics/imaging-summary`
- `GET /api/v1/export/patients-csv`

### 前端

新增 `统计` 页面：

- 队列概览。
- 处方分布。
- 治疗部位、技术、机器统计。
- 计划 CT / CBCT 归档统计。
- 患者级 CSV 导出按钮。

### 数据来源

- `patient_index`
- `mosaiq_prescription`
- `treatment_fraction`
- `image_archive`

## 暂缓到后续版本

- DVH 高级统计：等待 `dvh_metric` 批量抽取稳定。
- 摆位误差和 Van Herk margin：等待 `xvi_registration` couch shift 字段稳定。
- Kaplan-Meier 生存分析：等待 `clinical_outcome` 事件/删失/入组日期数据字典。
- HI/CI 计划质量：等待 D2/D50/D98、靶区体积和处方剂量体积数据。

## 安全约束

- 不返回患者姓名、身份证、电话、住址。
- 不返回原始 PatientID 或原始 UID。
- 导出 CSV 只包含脱敏研究字段。
- 生产部署前应增加登录、权限和审计。
