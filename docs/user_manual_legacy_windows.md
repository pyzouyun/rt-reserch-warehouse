# Win7/Win10 离线版用户使用手册

适用版本：`v0.2.0-win7-legacy`

## 1. 适用范围

目标系统：

- Windows 7 SP1 64 位
- Windows 10 64 位

本版本不依赖 Docker Desktop。运行时随安装包携带或预置：

- Python 3.8
- PostgreSQL 10
- Orthanc Windows runtime
- NSSM 服务管理工具
- Web 静态文件

说明：当前项目已生成 `legacy/staging/` 安装源目录，最终 `.exe` 安装器需要 Inno Setup 编译。Win7 SP1 仍需在真实或虚拟机环境中完成验证后，才能作为正式部署包发放。

## 2. 安装

正式安装包规划名称：

```text
RTResearchWarehouseLegacySetup-0.2.0.exe
```

安装步骤：

1. 以管理员身份运行安装包。
2. 选择安装目录，默认建议：

```text
C:\Program Files\RTResearchWarehouseLegacy
```

3. 等待安装器初始化配置、数据库和 Windows 服务。
4. 安装完成后重启电脑，或手动启动服务。

安装器会注册：

```text
RTResearch-PostgreSQL
RTResearch-Orthanc
RTResearch-API
```

## 3. 当前 staging 测试方式

如果还没有 `.exe` 安装包，但已有：

```text
legacy/staging/
```

可以复制到测试机，例如：

```text
C:\RTResearchWarehouseLegacy
```

以管理员身份打开 PowerShell：

```powershell
cd C:\RTResearchWarehouseLegacy
powershell -ExecutionPolicy Bypass -File scripts\init-config.ps1
powershell -ExecutionPolicy Bypass -File scripts\init-postgres.ps1
powershell -ExecutionPolicy Bypass -File scripts\install-services.ps1
powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1
```

这种方式用于内部测试，不如正式安装包友好。

## 4. 访问地址

- Web 工作台：`http://localhost:8080`
- API：`http://localhost:8080/api/v1`
- API 文档：`http://localhost:8080/docs`
- Orthanc Web：`http://localhost:8042`
- DICOM C-STORE：`4242`
- PostgreSQL：`127.0.0.1:5432`

Orthanc 用户名和密码位于安装目录：

```text
config\.env
```

不要把该文件发送给无权限人员。

## 5. 启动和停止

启动全部服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-all.ps1
```

停止全部服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop-all.ps1
```

查看服务状态：

```powershell
Get-Service RTResearch-*
```

## 6. 接收 DICOM

在 Monaco、XVI、Elekta 相关 DICOM 节点或测试发送工具中配置：

```text
Called AE Title: RT_RESEARCH
Host: 安装本系统的电脑 IP
Port: 4242
```

防火墙应允许 `4242/tcp` 用于 DICOM C-STORE。管理端口 `8080`、`8042`、`5432` 默认建议仅本机访问。

## 7. 运行 ETL

Orthanc 收到 DICOM 后，在安装目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run-etl.ps1
```

ETL 会读取 Orthanc 中的 DICOM，解析基础信息并写入 PostgreSQL。

## 8. 导入 MOSAIQ CSV

CSV 模板位于：

```text
data_templates\
```

导入：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\import-mosaiq.ps1
```

CSV 文件中不要保存患者姓名、身份证、电话、住址等直接身份标识。

## 9. V2 工作台常用操作

- 患者索引：查看详情、编辑研究状态、新增结局。
- MOSAIQ：校验/导入 CSV，新增/编辑/删除分次和流程记录。
- 结局：新增/编辑/删除研究侧临床结局。
- DICOM/RT 数据：查看脱敏后的影像和放疗对象摘要。

可编辑数据仅限研究侧表，不写回 Monaco、MOSAIQ、XVI 或加速器。

## 10. 备份和恢复

备份：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup.ps1
```

恢复：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\restore.ps1 -BackupDir "备份目录路径"
```

建议同时备份：

```text
data\postgres\
data\orthanc\
config\.env
```

`config\.env` 包含脱敏 salt 和服务密码，必须加密保存。

## 11. 卸载

正式安装包可通过 Windows 控制面板卸载。

staging 测试环境可先停止并删除服务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop-all.ps1
powershell -ExecutionPolicy Bypass -File scripts\uninstall-services.ps1
```

删除安装目录前，必须确认已备份 `data\` 和 `config\.env`。

## 12. 常见问题

### Web 页面打不开

检查服务：

```powershell
Get-Service RTResearch-*
```

查看日志：

```text
logs\api-service.err.log
logs\api-service.log
```

### Orthanc 打不开或 DICOM 发不进来

检查：

- `RTResearch-Orthanc` 服务是否运行。
- `4242/tcp` 是否被防火墙拦截。
- DICOM 节点 AE Title 是否为 `RT_RESEARCH`。
- 是否有其他 Orthanc 或 DICOM 服务占用 `8042` 或 `4242`。

### PostgreSQL 启动失败

检查：

- `RTResearch-PostgreSQL` 服务是否运行。
- `data\postgres\` 是否存在。
- `5432` 是否被其他 PostgreSQL 占用。
- 日志：`logs\postgres-service.err.log`。

### Win7 无法运行

Win7 已停止官方支持，常见问题包括缺少系统补丁、VC++ 运行库、安全软件阻止服务安装、PowerShell 版本过旧、新版 Orthanc runtime 不兼容 Win7。

如在 Win7 中失败，应先记录错误日志，再考虑更换较旧 Orthanc Windows runtime。

## 13. 数据安全

- 系统只处理研究副本，不写回临床系统。
- 不保存姓名、身份证、电话、住址等直接身份标识。
- 限制局域网访问，尤其是 Orthanc Web、API 和 PostgreSQL。
- 定期备份，并做恢复演练。
- 使用前应完成伦理审批、数据使用授权和院内安全评估。
