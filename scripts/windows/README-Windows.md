# RT Research Warehouse Windows Installer

This package installs the radiotherapy research data warehouse on a Windows computer.

## What Is Included

- Application source files
- FastAPI API container image
- React Web UI container image
- Python ETL container image
- Orthanc, PostgreSQL, and pgAdmin container images
- Install, start, stop, and uninstall scripts

The target computer does not need Python, Node.js, PostgreSQL, or Orthanc installed locally.

## Required On Target Computer

- Windows 10/11 or Windows Server with Docker Desktop or Docker Engine
- Docker Desktop must be started before installation
- Administrator PowerShell is recommended

Docker Desktop is not bundled in this package. If Docker is missing and `winget` is available, you can run:

```powershell
.\install.ps1 -InstallDockerWithWinget
```

After Docker Desktop is installed, start it once and rerun:

```powershell
.\install.ps1
```

## Install

1. Unzip this package.
2. Open PowerShell as Administrator.
3. Allow scripts for this session:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

4. Run:

```powershell
.\install.ps1
```

The installer creates a local `.env` with random passwords and a random de-identification salt.

## Open

- Web UI: <http://localhost:8080>
- Orthanc: <http://localhost:8042>
- API docs: <http://localhost:8000/docs>

Desktop shortcuts are created for start and stop.
The same scripts are also copied to the installation directory, by default `C:\ProgramData\RTResearchWarehouse`.

## Start Later

```powershell
.\start.ps1
```

## Stop

```powershell
.\stop.ps1
```

## Uninstall

Keep Docker volumes:

```powershell
.\uninstall.ps1
```

Remove application and data volumes:

```powershell
.\uninstall.ps1 -RemoveData
```

Use `-RemoveData` carefully. It deletes PostgreSQL and Orthanc Docker volumes.

## Security Notes

- Do not share the generated `.env` file casually.
- Keep `DEIDENTIFY_SALT` stable for a site; changing it changes pseudonymous patient mapping.
- This prototype is intended for approved research workflows and does not write back to Monaco, MOSAIQ, XVI, or linac systems.
