# 放疗研究数据仓库原型

这是一个只读的放疗研究数据仓库原型，用于整合 Monaco 计划系统、MOSAIQ 流程数据、Elekta 加速器相关数据和 XVI/CBCT DICOM 数据。

系统不会写回 Monaco、MOSAIQ、XVI 或加速器。所有患者标识进入研究库前都应脱敏。

当前源码版本：`0.2.0-statistics`

## 架构

- Orthanc：DICOM C-STORE 接收、DICOM 存储、REST API。
- PostgreSQL：结构化研究数据库。
- Python ETL：读取 Orthanc，解析 CT/CBCT/RTSTRUCT/RTPLAN/RTDOSE/REG 基础元数据，生成脱敏研究索引并入库。
- FastAPI：为 Web 工作台提供查询、ETL 触发和研究侧 CRUD API。
- React Web：可视化研究工作台。
- MOSAIQ CSV importer：通过 CSV 模板导入 MOSAIQ 研究副本，不直连生产库。

## 快速启动

```powershell
Copy-Item .env.example .env
# 编辑 .env，替换所有密码和 DEIDENTIFY_SALT
docker compose up -d postgres orthanc api web
```

访问：

- Web 工作台：`http://localhost:8080`
- API 文档：`http://localhost:8000/docs`
- Orthanc Web：`http://localhost:8042`
- DICOM C-STORE：`4242`

Orthanc DICOM 配置：

```text
Called AE Title: RT_RESEARCH
Host: 部署本项目的电脑或服务器 IP
Port: 4242
```

## 运行 ETL

Orthanc 收到 DICOM 后运行：

```powershell
docker compose --profile etl run --rm etl python -m etl.run_etl
```

ETL 会写入：

- `patient_index`
- `dicom_study`
- `dicom_series`
- `dicom_instance`
- `image_archive`
- `rt_structure`
- `rt_plan`
- `rt_dose`
- `xvi_registration`
- `etl_log`

## XVI/CBCT 归档

当前版本支持按 DICOM Series 归档计划 CT、XVI CBCT 和未分类 CT。一个患者可以有多个计划 CT 和多个 CBCT。

查看方式：

- Web 工作台：进入 `XVI/CBCT`
- API：`GET /api/v1/xvi/image-archive`
- 仅 CBCT：`GET /api/v1/xvi/cbct-series`

原始 DICOM 文件仍由 Orthanc 保存，PostgreSQL 只保存脱敏索引和基础元数据。

## MOSAIQ CSV

模板位于：

```text
data_templates/
```

导入：

```powershell
docker compose --profile etl run --rm etl python -m etl.import_mosaiq_csv /app/data_templates
```

CSV 中不要包含姓名、身份证、电话、住址等直接身份标识。

## 脱敏原则

`.env` 中必须配置稳定且足够长的 `DEIDENTIFY_SALT`。ETL 会生成：

- `research_patient_id`
- `patient_id_hash`
- `study_instance_uid_hash`
- `series_instance_uid_hash`
- `sop_instance_uid_hash`
- `accession_number_hash`
- `frame_of_reference_uid_hash`

不要把 `.env`、数据库备份或 Orthanc 存储目录发给无权限人员。

## 文档

- 使用文档：[docs/usage_guide.md](docs/usage_guide.md)
- Docker 用户手册：[docs/user_manual_docker.md](docs/user_manual_docker.md)
- 可视化界面说明：[docs/ui_guide.md](docs/ui_guide.md)
- XVI/CBCT 归档说明：[docs/xvi_cbct_archive.md](docs/xvi_cbct_archive.md)
- 统计模块技术设计：[docs/statistics_v0.2_technical_design.md](docs/statistics_v0.2_technical_design.md)
- 数据库结构：[docs/database_schema.md](docs/database_schema.md)
- DICOM 流程：[docs/dicom_workflow.md](docs/dicom_workflow.md)
- 安全与脱敏：[docs/security_and_deidentification.md](docs/security_and_deidentification.md)
- 当前版本发布说明：[docs/releases/v0.2.0-statistics.md](docs/releases/v0.2.0-statistics.md)
- Docker v0.1.1 发布说明：[docs/releases/v0.1.1-docker.md](docs/releases/v0.1.1-docker.md)
- Win7/Win10 离线版手册：[docs/user_manual_legacy_windows.md](docs/user_manual_legacy_windows.md)

## 开发验证

```powershell
C:\Users\zy\miniconda3\python.exe -m pytest tests api/tests -q
C:\Users\zy\miniconda3\python.exe -m compileall -q etl api\app
cd web
npm run build
```

## 数据安全

本项目仅用于经批准的研究数据或测试数据。生产环境应增加登录认证、角色权限、HTTPS、审计日志、备份恢复演练和院内伦理/数据使用审批流程。
