param(
    [string]$OutputRoot = "legacy\output",
    [string]$StagingRoot = "legacy\staging",
    [switch]$SkipWebBuild
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Path {
    param([string]$Path, [string]$Message)
    if (-not (Test-Path $Path)) {
        throw "$Message Missing path: $Path"
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$staging = Join-Path $repoRoot $StagingRoot
$output = Join-Path $repoRoot $OutputRoot

Write-Step "Checking required legacy runtimes"
Assert-Path (Join-Path $repoRoot "legacy\runtime\python38\python.exe") "Python 3.8 runtime is required."
Assert-Path (Join-Path $repoRoot "legacy\runtime\postgres\bin\postgres.exe") "PostgreSQL runtime is required."
Assert-Path (Join-Path $repoRoot "legacy\runtime\orthanc\Orthanc.exe") "Orthanc runtime is required."
Assert-Path (Join-Path $repoRoot "legacy\runtime\nssm") "NSSM runtime is required."

if (-not $SkipWebBuild) {
    Write-Step "Building Web UI"
    Push-Location (Join-Path $repoRoot "web")
    try {
        $env:VITE_API_BASE_URL = "/api/v1"
        npm install
        npm run build
    } finally {
        Pop-Location
    }
}

Write-Step "Creating staging directory"
if (Test-Path $staging) {
    Remove-Item -Recurse -Force $staging
}
New-Item -ItemType Directory -Force $staging | Out-Null

foreach ($dir in @("etl", "sql", "data_templates", "legacy\scripts", "legacy\config", "legacy\runtime")) {
    Copy-Item -Recurse -Force (Join-Path $repoRoot $dir) (Join-Path $staging (Split-Path $dir -Leaf))
}
Copy-Item -Recurse -Force (Join-Path $repoRoot "api\app") (Join-Path $staging "app")
Copy-Item -Force (Join-Path $repoRoot "legacy\requirements-py38.txt") $staging
Copy-Item -Force (Join-Path $repoRoot "legacy\VERSION") $staging
Copy-Item -Recurse -Force (Join-Path $repoRoot "web\dist") (Join-Path $staging "web")

Write-Step "Preparing output directory"
New-Item -ItemType Directory -Force $output | Out-Null

Write-Host ""
Write-Host "Legacy staging prepared:" -ForegroundColor Green
Write-Host $staging
Write-Host ""
Write-Host "Next: build installer with Inno Setup using legacy\installer\RTResearchWarehouseLegacy.iss"
