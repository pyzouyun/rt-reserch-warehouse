# XVI CBCT 图像导入和归档

本功能用于把 XVI/Elekta CBCT 与 Monaco 计划 CT 作为研究侧影像资产进行归档。原始 DICOM 文件仍存放在 Orthanc，PostgreSQL 只保存脱敏索引、分类结果和基础元数据。

## 数据流

1. Monaco、XVI 或 Elekta DICOM 节点把 DICOM 发送到 Orthanc。
2. 运行 Orthanc ETL。
3. ETL 解析 DICOM metadata。
4. CT-like series 写入 `image_archive`。
5. Web 工作台 `XVI/CBCT` 页面展示归档记录。

## 归档粒度

归档按 DICOM Series 去重，不按单张 slice 建一条记录。一个患者可以有：

- 多个计划 CT。
- 多个 XVI CBCT。
- 多个未分类 CT。

每条归档记录包含：

- `research_patient_id`
- `image_role`
- `source_system`
- `acquisition_date`
- `acquisition_time`
- `series_instance_uid_hash`
- `frame_of_reference_uid_hash`
- `study_description`
- `series_description`
- `orthanc_instance_id`
- `metadata`

## 分类规则

当前为最小可运行规则：

- 描述中包含 `cbct`、`xvi`、`cone beam`、`conebeam`、`kvct`、`kvcbct`、`volumeview` 时归为 `cbct`。
- 描述中包含 `planning`、`plan ct`、`simulation`、`sim ct`、`ct sim`、`定位`、`monaco` 时归为 `planning_ct`。
- 其他 CT 归为 `unknown_ct`。

分类依据来自 `StudyDescription`、`SeriesDescription`、`ProtocolName`、`Manufacturer`、`ManufacturerModelName` 和 `StationName`。这些字段可能因医院导出规范不同而变化，正式使用前应根据本院 XVI 导出样例调整规则。

## 使用方法

发送 DICOM：

```text
Called AE Title: RT_RESEARCH
Host: 部署本项目的电脑或服务器 IP
Port: 4242
```

运行 ETL：

```powershell
docker compose --profile etl run --rm etl python -m etl.run_etl
```

查看：

- Web：打开 `http://localhost:8080`，进入 `XVI/CBCT`。
- API：`GET http://localhost:8000/api/v1/xvi/image-archive`
- 仅 CBCT：`GET http://localhost:8000/api/v1/xvi/cbct-series`

## 安全边界

- 不写回 Monaco、MOSAIQ、XVI 或加速器。
- 不保存姓名、身份证、电话、住址。
- 不把 Orthanc 原始影像暴露给无权限人员。
- 若需要导出 NIfTI、NRRD 或 DICOM 子集，应另行增加权限、审计和脱敏流程。
