# Win7 无 Docker 离线安装版设计文档

## 目标

创建一个不依赖 Docker Desktop、支持 Windows 7 64 位、可离线直接安装和启动的放疗研究数据仓库版本。

目标版本建议命名：

```text
v0.2.0-win7-legacy
```

该版本应与当前 Docker 版 `v0.1.0-docker` 分开维护，避免为了兼容 Win7 牺牲 Docker 版的现代部署方式。

## 关键限制

Windows 7 已停止官方支持，很多现代运行时无法直接使用：

- Docker Desktop 不支持 Windows 7。
- Python 3.11 不支持 Windows 7。
- 当前 ETL/API 代码使用了 Python 3.10+ 语法，例如 `str | None`。
- 现代 PostgreSQL、Orthanc、浏览器和 TLS 组件对 Win7 的支持有限。
- Win7 机器常见医院内网策略可能限制服务安装、防火墙端口、VC++ 运行库和 PowerShell 版本。

因此 Win7 版本需要作为“legacy portable runtime”单独设计。

## 已确认约束

用户已确认：

- 目标系统：Windows 7 SP1 64 位。
- 允许安装 Windows 服务。
- 预计存储病例量：1000 例以上。
- 不要求内置便携浏览器。
- DICOM 端口 `4242` 可以对局域网开放。

基于以上约束，推荐路线为：

- 继续优先使用 PostgreSQL 便携版，而不是 SQLite。
- 使用 Windows 服务方式运行 PostgreSQL、Orthanc 和 API。
- Web UI 使用目标电脑已有浏览器打开。
- 安装器需要配置 Windows 防火墙规则，至少开放 Orthanc DICOM C-STORE 端口 `4242`，并默认仅本机开放管理端口。

## Win7 / Win10 双兼容版本矩阵

目标是同一个 legacy 安装包同时支持：

- Windows 7 SP1 64 位
- Windows 10 64 位

推荐第一版锁定如下运行时：

| 组件 | 推荐版本 | 选择原因 | 状态 |
| --- | --- | --- | --- |
| Python | 3.8.10 x64 | Python 官方文档提示需要 Windows 7 支持时安装 Python 3.8；3.8.10 是常用的 Win7 最后一批官方 Windows installer 版本 | 待 Win7 VM 验证 |
| PostgreSQL | 10.23 x64 binaries | EDB 仍提供 PostgreSQL 10.23 binaries；PostgreSQL 10 Windows 构建文档覆盖 Windows 7 SP1 到后续 Windows；适合 1000+ 病例规模 | 待 Win7 VM 验证 |
| Orthanc | 1.11.3 x64 Windows release 优先；如不兼容则降级到旧 Windows installer 系列 | 1.11.3 API 足够支持本项目所需 REST、C-STORE、DICOM 存储；比最新 1.12.x 更适合 legacy 兼容测试 | 待 Win7 VM 验证 |
| API Server | Waitress 2.x 或 Uvicorn 0.20.x 左右 | 避免依赖过新的 Windows runtime；API 仅需本机 HTTP 服务 | 待依赖锁定 |
| Web UI | 预构建静态文件 | 目标机不安装 Node.js；Win7/Win10 只需浏览器访问 | 已确定 |
| 服务管理 | NSSM 2.24 | 经典 Windows 服务封装工具，适合 Win7/Win10 | 待打包 |
| 安装器 | Inno Setup 6.3.x；如验证失败则改 NSIS 3.x | Inno Setup 6.3 起支持 Windows 7 及更新系统；满足 Win7/Win10 安装器目标 | 待安装器验证 |

重要说明：

- 以上版本以“兼容 Win7 + Win10”为优先级，不追求最新。
- PostgreSQL 10、Python 3.8、Win7 都已经不属于现代长期安全支持组合，因此该版本必须定位为受控内网 legacy 版本。
- 如果 Win7 VM 验证中 PostgreSQL 10.23 运行失败，才考虑 PostgreSQL 9.6.x 或 SQLite fallback。
- 如果 Orthanc 1.11.3 x64 在 Win7 上运行失败，优先测试 Orthanc Windows installer 历史版本，而不是改用 Docker。

## 版本资料来源

- Python 官方 Windows 文档提示：需要 Windows 7 支持时安装 Python 3.8。
- PostgreSQL Windows wiki 说明 PostgreSQL 支持 Windows XP 及以上，且 Windows 支持与版本发布周期相关。
- PostgreSQL 10 Windows 构建文档说明 Visual Studio 2017 到 2022 构建支持到 Windows 7 SP1 / Windows Server 2008 R2 SP1。
- EDB 下载页仍列出 PostgreSQL 10.23 binaries，但该版本已不在现代支持周期内。
- Orthanc 官方 Windows 下载页提供 Windows installer；Orthanc 1.11.3 有 Windows release 资源。
- Inno Setup 文档列出 Windows 7 版本号，社区资料显示 6.3 系列面向 Windows 7 及更新系统。

## 推荐架构

```text
RTResearchWarehouseLegacy/
  runtime/
    python38/
    orthanc/
    postgres/
    nssm/
  app/
    api/
    etl/
    web/
    sql/
    data_templates/
    logs/
  config/
    .env
    orthanc.json
    pg_hba.conf
    postgresql.conf
  data/
    postgres/
    orthanc/
  tools/
    start-all.bat
    stop-all.bat
    run-etl.bat
    import-mosaiq.bat
    backup.bat
    restore.bat
```

组件：

- Orthanc：使用 Windows 原生可执行文件或可移植发行包。
- PostgreSQL：内置可移植 PostgreSQL 运行时，数据目录放在 `data/postgres/`。
- API：改为 Python 3.8 兼容，使用 Waitress 或 Uvicorn 在本机运行。
- ETL：改为 Python 3.8 兼容，依赖随包安装到内置 virtualenv 或 wheelhouse。
- Web UI：在开发机预构建为静态文件，由 API 或轻量 HTTP server 提供。
- 服务管理：优先使用 NSSM 注册 Windows 服务；如果目标环境不允许装服务，则提供 `.bat` 启停脚本。

## 技术取舍

### 数据库

优先保留 PostgreSQL，原因：

- 当前数据库设计已经基于 PostgreSQL。
- 后续研究查询、JSONB、索引和多表关联更适合 PostgreSQL。
- 与 Docker 版数据模型保持一致。
- 1000 例以上病例会产生大量 DICOM instance、series、RT 对象、分次记录和后续 DVH 指标，PostgreSQL 更适合长期扩展。

备选方案是 SQLite，但不推荐作为第一版目标，因为它会造成 Docker 版和 Win7 版数据库能力分叉。只有在 PostgreSQL 便携版兼容性验证失败时，才考虑 SQLite fallback。

### Python

Win7 / Win10 双兼容版本建议使用 Python 3.8.10 x64 运行时。

需要改造：

- 把 `X | None` 类型写法改为 `Optional[X]`。
- 避免 Python 3.9+ 才有的标准库特性。
- 固定 FastAPI、SQLAlchemy、pydicom、pandas 等依赖到仍支持 Python 3.8 的版本。
- 生成离线 wheelhouse，目标电脑安装时不访问 PyPI。

### Web UI

开发机仍可用现代 Node.js 构建前端，但目标电脑不安装 Node。

目标电脑只运行：

- 静态 HTML/CSS/JS
- 本机 API 服务

浏览器要求：

- 推荐安装 Chrome / Edge / Firefox 的可运行版本。
- 不支持 IE。
- 本版本不内置便携浏览器。
- 如目标 Win7 环境没有现代浏览器，安装说明中提示用户自行安装可用浏览器；后续可另做带浏览器的变体。

## 安装方式

推荐使用 Inno Setup 或 NSIS 生成传统 Windows 安装包：

```text
RTResearchWarehouseLegacySetup-0.2.0.exe
```

安装流程：

1. 解压应用与运行时到 `C:\RTResearchWarehouseLegacy` 或用户指定目录。
2. 生成 `.env`，包含随机密码和 `DEIDENTIFY_SALT`。
3. 初始化 PostgreSQL 数据目录。
4. 执行 `sql/001_init.sql`。
5. 写入 Orthanc 配置。
6. 注册或启动服务：
   - `RTResearch-PostgreSQL`
   - `RTResearch-Orthanc`
   - `RTResearch-API`
7. 创建桌面快捷方式：
   - 打开 Web UI
   - 启动服务
   - 停止服务
   - 运行 ETL
   - 导入 MOSAIQ CSV

## 端口规划

保持与 Docker 版一致，降低培训成本：

- Web UI：`8080`
- API：`8080/api/v1`，legacy 版由同一个 FastAPI 服务同时提供 Web UI 和 API，减少 Win7 原生代理组件
- Orthanc Web：`8042`
- Orthanc DICOM：`4242`
- PostgreSQL：`5432`

如端口被占用，安装器应允许修改。

## 离线包内容

离线安装包需要包含：

- 应用代码
- 预构建 Web 静态文件
- Python 3.8 运行时
- Python wheels
- Orthanc Windows 运行时
- PostgreSQL Windows 运行时
- NSSM 或等价服务管理工具
- VC++ Runtime，如所选二进制需要
- 初始化 SQL
- 示例 CSV 模板
- 使用文档

## 安全要求

- 安装时生成随机密码，不写死默认密码。
- `.env` 默认只允许本机服务读取。
- Orthanc REST 开启认证。
- PostgreSQL 默认只监听本机，除非用户明确开启局域网访问。
- DICOM C-STORE 端口可按需开放到局域网。
- 不保存患者姓名、身份证、电话、住址。
- 不写回临床系统。

## 实施任务

### 阶段 1：兼容性评估

- 目标系统范围固定为 Win7 SP1 64 位。
- 使用 Windows 服务方式运行后台组件。
- 不内置浏览器，默认使用目标电脑已有浏览器。
- 确认 PostgreSQL 便携运行版本。
- 确认 Orthanc Windows 运行版本。

### 阶段 2：代码兼容 Python 3.8

- 新建 legacy 分支。
- 调整 API/ETL 类型注解语法。
- 固定 Python 3.8 依赖版本。
- 添加 Python 3.8 测试环境。

### 阶段 3：本机运行时打包

- 创建 `legacy/` 打包目录。
- 下载或放置 Python、PostgreSQL、Orthanc 运行时。
- 准备 wheelhouse。
- 编写 start/stop/init/backup 脚本。

### 阶段 4：安装器

- 编写 Inno Setup 或 NSIS 脚本。
- 安装时生成 `.env`。
- 初始化数据库。
- 注册服务和快捷方式。
- 配置 Windows 防火墙规则：
  - 开放 `4242/tcp` 给局域网 DICOM C-STORE。
  - `8080/8042/5432` 默认仅本机访问，除非用户显式选择开放。
- 生成卸载逻辑。

### 阶段 5：验证

- 在干净 Win7 SP1 64 位虚拟机测试。
- 断网安装测试。
- 重启后服务自启动测试。
- DICOM C-STORE 接收测试。
- MOSAIQ CSV 导入测试。
- ETL 入库测试。
- 卸载保留数据和彻底删除数据测试。

## 风险

- Win7 运行时兼容性是最大风险。
- Orthanc 官方新版本可能不再支持 Win7，需要锁定旧版或自行验证。
- PostgreSQL 新版本可能不支持 Win7，需要选择旧版并接受安全维护成本。
- Python 3.8 已进入安全维护末期或停止维护，需要在受控内网环境使用。
- 医院终端安全策略可能阻止服务安装或端口开放。

## 建议执行顺序

1. 准备 Win7 SP1 64 位测试虚拟机。
2. 验证 PostgreSQL 便携版可初始化、启动、停止和重启恢复。
3. 验证 Orthanc Windows 原生版可接收 DICOM C-STORE。
4. 做 Python 3.8 代码兼容。
5. 构建 Web 静态文件并由 API 提供。
6. 编写服务注册和防火墙配置脚本。
7. 制作 Inno Setup 或 NSIS 安装器。
8. 做断网安装、重启、自启动、ETL、CSV 导入、卸载验证。

## 执行计划草案

### Task 1：建立 legacy 目录和版本线

- 新建 `legacy/` 目录。
- 新建 `docs/releases/v0.2.0-win7-legacy.md`。
- 保留 Docker 版 `v0.1.0-docker` 不变。
- 新增 legacy README，明确 Win7 版运行边界。

### Task 2：Python 3.8 兼容改造

- 将 API 和 ETL 中的 `X | None` 改为 `Optional[X]`。
- 固定 legacy 依赖版本。
- 以 Python 3.8.10 x64 为目标解释器。
- 新增 Python 3.8 兼容测试说明。
- 避免破坏 Docker 版，可通过共享代码兼容 Python 3.8 和 3.11。

### Task 3：PostgreSQL 便携运行时

- 首选 PostgreSQL 10.23 x64 binaries。
- 编写 `init-postgres.ps1` 或 `.bat`。
- 数据目录放入 `data/postgres/`。
- 默认仅监听 `127.0.0.1`。
- 若 PostgreSQL 10.23 在 Win7 SP1 验证失败，再评估 PostgreSQL 9.6.x 或 SQLite fallback。

### Task 4：Orthanc Windows 运行时

- 首选 Orthanc 1.11.3 x64 Windows release。
- 生成 `orthanc.json`。
- 开启 AE Title `RT_RESEARCH`、端口 `4242`、Web 端口 `8042`。
- 开启认证。
- 若 Orthanc 1.11.3 在 Win7 SP1 验证失败，再测试更早 Windows installer。

### Task 5：服务管理

- 使用 NSSM 注册：
  - `RTResearch-PostgreSQL`
  - `RTResearch-Orthanc`
  - `RTResearch-API`
- 提供 start/stop/restart/status 脚本。

### Task 6：安装器

- 首选 Inno Setup 6.3.x，安装器目标为 Windows 7 SP1 64 位及 Windows 10 64 位。
- 安装时生成随机密码和 `DEIDENTIFY_SALT`。
- 初始化数据库和 SQL schema。
- 创建桌面快捷方式。
- 写入卸载逻辑。

### Task 7：离线验证

- 在断网 Win7 SP1 64 位虚拟机安装。
- 启动后访问 Web UI。
- 发送测试 DICOM 到 `4242`。
- 导入 MOSAIQ CSV。
- 跑 ETL。
- 重启系统确认服务恢复。
- 卸载并分别验证保留数据和删除数据两种路径。

## 暂停点

本文档完成后暂停，不立即执行实现。

需要用户确认以下问题后再开始：

- PostgreSQL 便携版本选择。
- Orthanc Windows 运行时版本选择。
- 安装器技术选择：Inno Setup 或 NSIS。
- 是否具备 Win7 SP1 64 位测试虚拟机。
