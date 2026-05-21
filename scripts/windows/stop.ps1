param(
    [string]$InstallDir = "$env:ProgramData\RTResearchWarehouse"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $InstallDir "docker-compose.yml"))) {
    throw "Application is not installed at $InstallDir"
}

Push-Location $InstallDir
try {
    docker compose -f docker-compose.yml -f docker-compose.installer.yml --env-file .env down
    Write-Host "RT Research Warehouse stopped." -ForegroundColor Green
} finally {
    Pop-Location
}
