# 放疗研究数据仓库使用文档

本项目用于搭建只读的放疗研究数据仓库，整合 Monaco、MOSAIQ、Elekta 加速器和 XVI 相关数据。临床源系统只读，不写回。

## 1. 当前能力

已经具备：

- Orthanc DICOM Server：接收和存储 DICOM，提供 REST API。
- PostgreSQL 研究数据库：保存脱敏后的结构化研究数据。
- Python ETL：从 Orthanc 扫描 DICOM，解析基础元数据并入库。
- DICOM 脱敏：PatientID、StudyInstanceUID、SeriesInstanceUID、SOPInstanceUID 使用 salted hash。
- XVI CBCT / 计划 CT 归档：按 DICOM Series 建立脱敏归档索引，支持一个患者多个 CBCT 和多个计划 CT。
- MOSAIQ CSV 导入：通过模板导入患者索引、处方、分次治疗和流程数据。
- Web 工作台：查看数据资产、DICOM、XVI/CBCT、RT 数据、MOSAIQ、结局和 ETL 日志。

当前仍属于原型版本，不包含生产级权限体系、审计平台、完整 DICOM-RT 字段解析、Elekta 私有日志解析或 AI 训练流水线。

## 2. 启动服务

进入项目目录：

```powershell
cd "C:\Users\zy\OneDrive\文档\New project"
```

如果没有 `.env`：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，至少设置：

```text
POSTGRES_PASSWORD
ORTHANC_PASSWORD
PGADMIN_DEFAULT_PASSWORD
DEIDENTIFY_SALT
```

启动：

```powershell
docker compose up -d postgres orthanc api web
```

访问：

- Web 工作台：`http://localhost:8080`
- API 文档：`http://localhost:8000/docs`
- Orthanc Web：`http://localhost:8042`
- DICOM C-STORE：`4242`

## 3. 发送 DICOM

在 Monaco、XVI 或 Elekta DICOM 节点中配置：

```text
Called AE Title: RT_RESEARCH
Host: 部署本项目的电脑或服务器 IP
Port: 4242
```

可发送：

- 计划 CT / 定位 CT
- XVI CBCT
- RTSTRUCT
- RTPLAN
- RTDOSE
- REG / RTIMAGE

## 4. 运行 DICOM ETL

Orthanc 收到 DICOM 后运行：

```powershell
docker compose --profile etl run --rm etl python -m etl.run_etl
```

ETL 会：

1. 调用 Orthanc REST API 获取所有 instance。
2. 使用 pydicom 读取 DICOM metadata。
3. 生成 `research_patient_id`。
4. 对 PatientID、StudyInstanceUID、SeriesInstanceUID、SOPInstanceUID 做 salted hash。
5. 写入 `patient_index`、`dicom_study`、`dicom_series`、`dicom_instance`。
6. 将计划 CT、XVI CBCT 和未分类 CT 写入 `image_archive`。
7. 将 RTSTRUCT、RTPLAN、RTDOSE、REG/RTIMAGE 摘要写入对应研究表。
8. 在 `etl_log` 中记录运行结果。

## 5. XVI/CBCT 归档

打开 Web 工作台 `XVI/CBCT` 页面，可以查看：

- 一个患者的多个计划 CT。
- 一个患者的多个 XVI CBCT。
- 未分类 CT。
- 采集日期、采集时间、来源系统、Series UID hash、FrameOfReference hash 和切片数。

API：

```text
GET /api/v1/xvi/image-archive
GET /api/v1/xvi/image-archive?research_patient_id=RP-xxx
GET /api/v1/xvi/image-archive?image_role=cbct
GET /api/v1/xvi/cbct-series
```

数据库查询示例：

```sql
SELECT research_patient_id, image_role, source_system, acquisition_date,
       series_description, series_instance_uid_hash
FROM image_archive
ORDER BY acquisition_date DESC NULLS LAST, updated_at DESC
LIMIT 20;
```

说明：原始 DICOM 图像仍由 Orthanc 保存，`image_archive` 只保存脱敏索引和基础元数据。

## 6. 导入 MOSAIQ CSV

CSV 模板在：

```text
data_templates/
```

推荐在 Web 工作台 `MOSAIQ` 页面点击 `校验 CSV`，确认通过后点击 `导入 CSV`。

命令行导入：

```powershell
docker compose --profile etl run --rm etl python -m etl.import_mosaiq_csv /app/data_templates
```

CSV 中不要包含姓名、身份证、电话、住址等直接身份标识。

## 7. Web 工作台

- 总览：查看患者、DICOM、RT、分次、影像归档统计。
- 患者索引：查看详情、编辑研究状态、新增结局。
- DICOM：浏览 Series。
- XVI/CBCT：查看计划 CT 和 CBCT 归档。
- RT 数据：查看 RT 对象和 DVH 指标。
- MOSAIQ：导入 CSV，维护研究侧分次和流程记录。
- 结局：维护研究侧临床结局。
- ETL：触发 ETL 并查看日志。

## 8. 备份

备份 PostgreSQL：

```powershell
docker compose exec postgres pg_dump -U rt_research rt_research > backup.sql
```

还应备份：

- `.env`
- `DEIDENTIFY_SALT`
- PostgreSQL volume
- Orthanc volume

`DEIDENTIFY_SALT` 必须妥善保存。丢失后，同一患者可能无法稳定映射到原来的脱敏 ID。

## 9. 数据安全

- 仅处理经批准的研究数据或测试数据。
- 不保存姓名、身份证、电话、住址等直接身份标识。
- 不写回 Monaco、MOSAIQ、XVI 或加速器。
- 生产部署前应增加登录认证、角色权限、HTTPS、审计日志和备份恢复演练。

## 10. 常见问题

### DICOM 发不进来

检查 AE Title、IP、端口 `4242`、防火墙和 Orthanc 容器状态。

### 患者匹配不上

通常是 Monaco DICOM、MOSAIQ CSV、XVI 导出使用了不同 PatientID。需要建立站点级映射策略，映射表也必须脱敏或受控保存。

### XVI CBCT 没被识别为 CBCT

当前分类依赖 `SeriesDescription`、`ProtocolName`、`Manufacturer` 等字段。如果本院 XVI 导出命名不同，应根据样例调整 `etl/parse_dicom.py` 中的分类关键词。
