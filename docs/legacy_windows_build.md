# Win7/Win10 无 Docker Legacy 版构建说明

本文档说明如何构建 `v0.2.0-win7-legacy` 安装包。

该版本目标：

- 支持 Windows 7 SP1 64 位
- 支持 Windows 10 64 位
- 不依赖 Docker Desktop
- 离线安装和离线运行

## 当前实现状态

已完成：

- API / ETL Python 3.8 语法兼容
- legacy 配置模板
- PostgreSQL 初始化脚本
- Orthanc 配置模板
- NSSM 服务注册脚本
- ETL / MOSAIQ CSV / 备份恢复脚本
- Inno Setup 安装器脚本
- legacy staging 构建脚本

仍需在制作最终安装器前准备第三方 runtime。

## 需要准备的 runtime

请将 runtime 解压或放置到：

```text
legacy/runtime/
```

期望结构：

```text
legacy/runtime/
  python38/
    python.exe
    Lib/
    Scripts/
  postgres/
    bin/
      postgres.exe
      pg_ctl.exe
      initdb.exe
      psql.exe
      pg_dump.exe
  orthanc/
    Orthanc.exe
  nssm/
    win64/
      nssm.exe
```

推荐版本：

- Python 3.8.10 x64
- PostgreSQL 10.23 x64 binaries
- Orthanc 1.11.3 x64 Windows release
- NSSM 2.24

## Python 依赖

legacy Python runtime 需要预先安装：

```text
legacy/requirements-py38.txt
```

建议在构建机上准备离线 wheelhouse，然后安装到 `legacy/runtime/python38/` 对应环境中。

目标电脑安装时不访问 PyPI。

可在联网的构建机上生成 wheelhouse：

```powershell
powershell -ExecutionPolicy Bypass -File legacy/download-wheelhouse.ps1
```

该脚本会按 Python 3.8 / Windows x64 下载二进制 wheel 到：

```text
legacy/wheelhouse/
```

## 准备 runtime

先把第三方源包放入：

```text
legacy/vendor/
```

推荐源包：

```text
python-3.8.10-amd64.exe
postgresql-10.23-1-windows-x64-binaries.zip
Orthanc-*.zip 或已解压的 Orthanc.exe 目录
OrthancInstaller-Win64-*.exe
nssm-2.24.zip
```

在联网构建机上可以用脚本下载这些源包：

```powershell
powershell -ExecutionPolicy Bypass -File legacy/download-vendor.ps1
```

下载后会生成：

```text
legacy/vendor/SHA256SUMS.txt
```

请在正式发放安装包前保留该校验清单，便于审计第三方二进制来源。

如果医院网络或代理阻断某些官方下载地址，脚本会列出缺失文件。此时可以手工从官方页面下载后放入 `legacy/vendor/`，再重新运行同一脚本生成校验清单。

然后运行：

```powershell
powershell -ExecutionPolicy Bypass -File legacy/prepare-runtime.ps1
```

该脚本会：

1. 静默安装 Python 到 `legacy/runtime/python38/`。
2. 从 `legacy/wheelhouse/` 离线安装 Python 依赖。
3. 解压 PostgreSQL binaries 到 `legacy/runtime/postgres/`。
4. 解压 Orthanc 到 `legacy/runtime/orthanc/`。
5. 解压 NSSM 到 `legacy/runtime/nssm/`。

说明：`OrthancInstaller-Win64-*.exe` 这类安装器可能会临时注册系统级 `Orthanc` 服务。`prepare-runtime.ps1` 会在复制安装目录后尝试停止并卸载该临时服务，最终项目安装包仍使用自己的 `RTResearch-Orthanc` 服务。

如果构建机允许联网，也可以临时使用：

```powershell
powershell -ExecutionPolicy Bypass -File legacy/prepare-runtime.ps1 -AllowOnlinePip
```

但正式制作离线安装包前，推荐使用 wheelhouse，这样目标电脑无需访问 PyPI。

## 构建 staging

```powershell
powershell -ExecutionPolicy Bypass -File legacy/build-legacy-package.ps1
```

该命令会：

1. 检查 `legacy/runtime/` 是否存在必要可执行文件。
2. 构建 Web UI。
3. 创建 `legacy/staging/`。
4. 复制 API、ETL、SQL、CSV 模板、配置、脚本、runtime 和 Web 静态文件。

## 构建安装器

安装 Inno Setup 6.3.x 后，可以直接运行：

```powershell
powershell -ExecutionPolicy Bypass -File legacy/build-installer.ps1
```

也可以手工打开：

```text
legacy/installer/RTResearchWarehouseLegacy.iss
```

编译后输出：

```text
legacy/output/RTResearchWarehouseLegacySetup-0.2.0.exe
```

## 安装后服务

安装器会注册：

- `RTResearch-PostgreSQL`
- `RTResearch-Orthanc`
- `RTResearch-API`

访问：

- Web UI：`http://localhost:8080`
- API：`http://localhost:8080/api/v1`
- API docs：`http://localhost:8080/docs`
- Orthanc：`http://localhost:8042`
- DICOM C-STORE：`4242/tcp`

## Win7 验证清单

必须在干净 Windows 7 SP1 64 位虚拟机中验证：

- 断网安装
- 服务注册
- 重启后服务恢复
- Web UI 打开
- Orthanc Web 打开
- DICOM C-STORE 接收
- ETL 入库
- MOSAIQ CSV 导入
- PostgreSQL 备份恢复
- 普通卸载保留数据
- 完全卸载删除数据

未完成 Win7 VM 验证前，不应宣称该安装器已达到生产可交付状态。
