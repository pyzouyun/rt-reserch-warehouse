# Research Workbench V2

V2 的目标是把常用研究操作放到可视化界面上，让用户不必频繁进入命令行，同时继续保持临床源系统只读。

## 核心入口

### 患者索引

用于研究队列管理。

按钮：

- 详情：查看患者脱敏索引、DICOM Study、治疗分次和流程状态。
- 编辑：维护研究状态，包括队列标签、纳入状态、审核状态、研究备注。
- 新增：为当前患者新增临床结局。

写入范围：

- 只更新 `patient_index.metadata.research_state`。
- 不修改 DICOM、Monaco、MOSAIQ、XVI 或加速器数据源。

### MOSAIQ

用于 CSV 导入和研究侧流程数据维护。

按钮：

- 校验 CSV：检查模板文件和必填表头。
- 导入 CSV：运行 MOSAIQ CSV ETL。
- 新增分次：新增 `treatment_fraction` 研究侧记录。
- 编辑分次：修改研究侧分次记录。
- 删除分次：删除研究侧分次记录。
- 新增流程：新增 `mosaiq_workflow` 研究侧记录。
- 编辑流程：修改研究侧流程记录。
- 删除流程：删除研究侧流程记录。

写入范围：

- `treatment_fraction`
- `mosaiq_workflow`
- ETL 导入后的 MOSAIQ 研究表

### 结局

用于维护疗效、毒性、随访等研究终点。

按钮：

- 新增结局
- 编辑结局
- 删除结局

写入范围：

- `clinical_outcome`

## 推荐工作流程

1. 从 Monaco、XVI 或加速器把 DICOM 发送到 Orthanc。
2. 在 ETL 页面运行 Orthanc ETL。
3. 在 MOSAIQ 页面校验并导入 CSV。
4. 在患者索引页面检查患者和研究状态。
5. 在结局页面录入或修正研究侧结局。
6. 使用 DICOM、RT 数据和 MOSAIQ 页面做数据核对。

## 安全要求

- 录入研究备注、结局值、流程状态时，不要填写姓名、身份证、电话、住址、病案号原文等直接身份信息。
- 删除按钮只用于研究侧记录，不能替代正式数据治理流程。
- 生产环境应配置用户登录、权限分级、操作审计、HTTPS 和定期备份。
