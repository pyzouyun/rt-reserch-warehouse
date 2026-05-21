# Windows 安装包制作与安装

本项目可以打包为 Windows 离线安装包。安装包包含应用文件和 Docker 镜像，目标电脑不需要安装 Python、Node.js、PostgreSQL 或 Orthanc。

## 交付形态

推荐交付文件：

```text
dist/RTResearchWarehouse-Windows.zip
```

解压后包含：

- `app/`：项目文件
- `images/rt-research-images.tar`：容器镜像包
- `install.ps1`：安装
- `start.ps1`：启动
- `stop.ps1`：停止
- `uninstall.ps1`：卸载
- `README-Windows.md`：目标电脑使用说明

## 为什么仍需要 Docker Desktop

Orthanc、PostgreSQL、API、Web UI 和 ETL 都以容器运行。这样可以把 Python、Node、PostgreSQL、Orthanc 等依赖封装在镜像里，避免污染目标电脑环境。

Docker Desktop 本身是运行时，通常不建议直接二次打包进医疗软件安装包中。安装脚本会检测 Docker；如果目标电脑缺少 Docker，可以使用：

```powershell
.\install.ps1 -InstallDockerWithWinget
```

## 在开发机制作安装包

开发机需要：

- Docker Desktop 已启动
- 网络可访问基础镜像仓库，首次打包需要拉取镜像

运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows/build-windows-package.ps1
```

或：

```bash
make package-windows
```

生成：

```text
dist/RTResearchWarehouse-Windows.zip
```

## 在目标电脑安装

1. 安装并启动 Docker Desktop。
2. 解压 `RTResearchWarehouse-Windows.zip`。
3. 以管理员身份打开 PowerShell。
4. 进入解压目录。
5. 运行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

安装完成后访问：

- Web UI：`http://localhost:8080`
- Orthanc：`http://localhost:8042`
- API 文档：`http://localhost:8000/docs`

安装脚本会把启动、停止和卸载脚本复制到默认安装目录：

```text
C:\ProgramData\RTResearchWarehouse
```

## 数据与卸载

默认数据保存在 Docker volumes 中，包括：

- PostgreSQL 研究数据库
- Orthanc DICOM 存储
- pgAdmin 数据

普通卸载保留 Docker volumes：

```powershell
.\uninstall.ps1
```

彻底删除应用和数据：

```powershell
.\uninstall.ps1 -RemoveData
```

`-RemoveData` 会删除数据库和 Orthanc 数据，请谨慎使用。
