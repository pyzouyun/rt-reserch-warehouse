param(
    [string]$InstallDir = "$env:ProgramData\RTResearchWarehouse",
    [switch]$InstallDockerWithWinget,
    [bool]$StartAfterInstall = $true
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function New-Secret {
    param([int]$Bytes = 24)
    $buffer = New-Object byte[] $Bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    return [Convert]::ToBase64String($buffer).Replace("+", "A").Replace("/", "B").Replace("=", "")
}

$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceApp = Join-Path $packageRoot "app"
$imageTar = Join-Path $packageRoot "images\rt-research-images.tar"

if (-not (Test-Path $sourceApp)) {
    throw "Cannot find app payload at $sourceApp"
}

Write-Step "Checking Docker Desktop"
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    if ($InstallDockerWithWinget) {
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if (-not $winget) {
            throw "Docker is missing and winget is unavailable. Install Docker Desktop first."
        }
        winget install --id Docker.DockerDesktop --source winget --accept-package-agreements --accept-source-agreements
        Write-Host "Docker Desktop was installed or queued. Restart Windows if required, start Docker Desktop, then run this installer again."
        exit 0
    }
    throw "Docker command not found. Install Docker Desktop, start it once, then rerun install.ps1. Or rerun with -InstallDockerWithWinget."
}

try {
    docker version | Out-Null
} catch {
    throw "Docker is installed but not running. Start Docker Desktop and rerun install.ps1."
}

Write-Step "Installing application files"
New-Item -ItemType Directory -Force $InstallDir | Out-Null
Copy-Item -Path (Join-Path $sourceApp "*") -Destination $InstallDir -Recurse -Force
Copy-Item -Force (Join-Path $packageRoot "start.ps1") $InstallDir
Copy-Item -Force (Join-Path $packageRoot "stop.ps1") $InstallDir
Copy-Item -Force (Join-Path $packageRoot "uninstall.ps1") $InstallDir
Copy-Item -Force (Join-Path $packageRoot "README-Windows.md") $InstallDir

Write-Step "Creating local environment file"
$envPath = Join-Path $InstallDir ".env"
if (-not (Test-Path $envPath)) {
    $postgresPassword = New-Secret
    $orthancPassword = New-Secret
    $pgadminPassword = New-Secret
    $salt = New-Secret -Bytes 32
@"
POSTGRES_DB=rt_research
POSTGRES_USER=rt_research
POSTGRES_PASSWORD=$postgresPassword
POSTGRES_PORT=5432

ORTHANC_USERNAME=orthanc
ORTHANC_PASSWORD=$orthancPassword
ORTHANC_DICOM_PORT=4242
ORTHANC_HTTP_PORT=8042
ORTHANC_URL=http://orthanc:8042

PGADMIN_DEFAULT_EMAIL=admin@example.org
PGADMIN_DEFAULT_PASSWORD=$pgadminPassword
PGADMIN_PORT=5050

DATABASE_URL=postgresql+psycopg2://rt_research:$postgresPassword@postgres:5432/rt_research
DEIDENTIFY_SALT=$salt
LOG_LEVEL=INFO
MOSAIQ_CSV_DIR=/app/data_templates

API_PORT=8000
WEB_PORT=8080
API_CORS_ORIGINS=http://localhost:5173,http://localhost:8080
VITE_API_BASE_URL=/api/v1
"@ | Set-Content -Path $envPath -Encoding UTF8
} else {
    Write-Host ".env already exists; keeping existing secrets."
}

Write-Step "Loading bundled Docker images"
if (Test-Path $imageTar) {
    docker load -i $imageTar
} else {
    Write-Warning "Image tar not found at $imageTar. Docker may pull/build images from the network."
}

Write-Step "Creating desktop shortcuts"
$desktop = [Environment]::GetFolderPath("Desktop")
$startShortcut = Join-Path $desktop "RT Research Warehouse - Start.lnk"
$stopShortcut = Join-Path $desktop "RT Research Warehouse - Stop.lnk"
$shell = New-Object -ComObject WScript.Shell

$shortcut = $shell.CreateShortcut($startShortcut)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$InstallDir\start.ps1`" -InstallDir `"$InstallDir`""
$shortcut.WorkingDirectory = $InstallDir
$shortcut.Save()

$shortcut = $shell.CreateShortcut($stopShortcut)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$InstallDir\stop.ps1`" -InstallDir `"$InstallDir`""
$shortcut.WorkingDirectory = $InstallDir
$shortcut.Save()

if ($StartAfterInstall) {
    Write-Step "Starting application"
    & (Join-Path $packageRoot "start.ps1") -InstallDir $InstallDir
}

Write-Host ""
Write-Host "Installation complete." -ForegroundColor Green
Write-Host "Web UI: http://localhost:8080"
Write-Host "Orthanc: http://localhost:8042"
Write-Host "API docs: http://localhost:8000/docs"
