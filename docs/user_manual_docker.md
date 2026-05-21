# Docker 版用户使用手册

适用版本：`v0.1.1-docker`

## 1. 环境要求

- Windows 10/11 64 位，或可运行 Docker Engine 的服务器。
- Docker Desktop 已启动，并使用 Linux containers。
- 浏览器：Edge、Chrome 或 Firefox。

本版本不需要单独安装 Python、Node.js、PostgreSQL、Orthanc 或 pgAdmin。

## 2. 首次启动

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

查看状态：

```powershell
docker compose ps
```

## 3. 访问地址

- Web 工作台：`http://localhost:8080`
- API 文档：`http://localhost:8000/docs`
- API 健康检查：`http://localhost:8000/api/v1/health`
- Orthanc Web：`http://localhost:8042`
- DICOM C-STORE：`4242`
- PostgreSQL：`localhost:5432`

Orthanc 登录账号来自 `.env` 中的 `ORTHANC_USERNAME` 和 `ORTHANC_PASSWORD`。

## 4. 接收 DICOM

在 Monaco、XVI、Elekta 相关 DICOM 节点或测试发送工具中配置：

```text
Called AE Title: RT_RESEARCH
Host: 本机或服务器 IP
Port: 4242
```

建议先发送测试病例或研究副本。系统只读处理研究数据，不向临床系统写回。

## 5. 运行 ETL

在 Web 工作台打开 `ETL` 页面，点击 `Orthanc ETL`。

也可以使用命令：

```powershell
docker compose --profile etl run --rm etl python -m etl.run_etl
```

## 6. 导入 MOSAIQ CSV

CSV 模板位于：

```text
data_templates/
```

包括：

```text
mosaiq_patient.csv
mosaiq_prescription.csv
mosaiq_fraction.csv
mosaiq_workflow.csv
```

推荐在 Web 工作台 `MOSAIQ` 页面先点击 `校验 CSV`，确认通过后点击 `导入 CSV`。

也可以使用命令：

```powershell
docker compose --profile etl run --rm etl python -m etl.import_mosaiq_csv /app/data_templates
```

CSV 中不要写入姓名、身份证、电话、住址等直接身份标识。

## 7. V2 工作台常用操作

- 患者索引：查看详情、编辑研究状态、新增结局。
- XVI/CBCT：查看计划 CT 和 XVI CBCT 归档，支持一个患者多个 CBCT 和多个计划 CT。
- MOSAIQ：校验/导入 CSV，新增/编辑/删除分次和流程记录。
- 结局：新增/编辑/删除研究侧临床结局。
- DICOM/RT 数据：查看脱敏后的影像和放疗对象摘要。

可编辑数据仅限研究侧表，不写回 Monaco、MOSAIQ、XVI 或加速器。

## 8. 停止和日志

停止但保留数据：

```powershell
docker compose down
```

查看日志：

```powershell
docker compose logs -f
```

## 9. 备份

备份 PostgreSQL：

```powershell
docker compose exec postgres pg_dump -U rt_research rt_research > backup.sql
```

生产或长期研究环境还应备份：

```text
postgres-data
orthanc-storage
.env
```

必须妥善保存 `.env` 中的 `DEIDENTIFY_SALT`。salt 丢失后，同一患者可能无法稳定映射到原来的脱敏研究 ID。

## 10. 常见问题

### 缺少 ORTHANC_PASSWORD 或 POSTGRES_PASSWORD

说明 `.env` 不存在或变量为空。复制 `.env.example` 后填写随机密码。

### Orthanc 返回 401

这是启用认证后的正常现象。使用 `.env` 中的 Orthanc 账号密码登录。

### 端口被占用

检查 `.env` 中的端口：

```text
ORTHANC_DICOM_PORT=4242
ORTHANC_HTTP_PORT=8042
POSTGRES_PORT=5432
API_PORT=8000
WEB_PORT=8080
```

修改后重启：

```powershell
docker compose down
docker compose up -d postgres orthanc api web
```

## 11. 数据安全

- 仅处理经批准的研究数据或测试数据。
- 不导入姓名、身份证、电话、住址等直接身份标识。
- 不把 `.env`、数据库备份、Orthanc 存储目录发给无权限人员。
- 院内部署前应完成伦理审批、数据使用授权、网络访问控制和备份恢复演练。
