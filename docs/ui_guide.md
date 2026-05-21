# 可视化研究工作台使用说明

本项目提供一个面向放疗研究数据仓库的 Web 工作台，用于查看脱敏 DICOM、RT、MOSAIQ CSV、ETL 日志，并维护研究侧数据。界面不会写回 Monaco、MOSAIQ、XVI 或加速器系统。

## 启动

先确认项目根目录已有 `.env`，并已设置 `POSTGRES_PASSWORD`、`ORTHANC_PASSWORD`、`DEIDENTIFY_SALT` 等配置。

```powershell
docker compose up -d postgres orthanc api web
```

访问地址：

- Web 工作台：`http://localhost:8080`
- API 文档：`http://localhost:8000/docs`
- API 健康检查：`http://localhost:8000/api/v1/health`

## 页面说明

### 总览

查看患者、Study、Series、Instance、RTSTRUCT、RTPLAN、RTDOSE、治疗分次等统计信息，以及最近 ETL 日志。

### 患者索引

按 `research_patient_id` 查询患者研究索引。页面只显示脱敏 ID、hash、性别和出生年，不显示姓名、身份证、电话或住址。

可用操作：

- 查看详情：查看该患者的 Study、分次和流程记录。
- 编辑研究状态：维护队列标签、纳入状态、审核状态和研究备注。
- 新增结局：为该患者新增研究侧临床结局。

### DICOM

浏览已入库的 DICOM Series，可按模态过滤 CT、RTSTRUCT、RTPLAN、RTDOSE、REG 等对象。

### XVI/CBCT

查看计划 CT、XVI CBCT 和未分类 CT 归档。页面按 DICOM Series 去重，支持按 `research_patient_id` 和影像类型筛选；一个患者可以有多条计划 CT 和多条 CBCT 记录。

### RT 数据

浏览 RTSTRUCT、RTPLAN、RTDOSE 摘要记录和 DVH 指标。

### MOSAIQ

查看 CSV 导入的处方、治疗分次和流程状态。

可用操作：

- 校验 CSV：检查 `data_templates/` 中 MOSAIQ CSV 文件是否存在、表头是否匹配模板。
- 导入 CSV：调用后端 ETL 导入 MOSAIQ CSV。
- 新增/编辑/删除分次：维护研究侧 `treatment_fraction` 记录。
- 新增/编辑/删除流程：维护研究侧 `mosaiq_workflow` 记录。

### 结局

维护研究侧 `clinical_outcome` 数据。支持新增、编辑、删除。不要在结局值中录入姓名、身份证、电话、住址等直接身份信息。

### ETL

触发 Orthanc DICOM ETL 或 MOSAIQ CSV 导入，并查看 `etl_log`。

### 安全

查看当前原型的数据边界和脱敏原则。

## 数据边界

- 临床源系统只读：Monaco、MOSAIQ、XVI、加速器数据只进入研究库，不写回。
- 可编辑数据仅限研究侧表：`clinical_outcome`、`patient_index.metadata.research_state`、`treatment_fraction`、`mosaiq_workflow`。
- 不保存明文姓名、身份证、电话、住址。
- 生产使用前应增加登录认证、角色权限、HTTPS、审计日志和备份恢复演练。
