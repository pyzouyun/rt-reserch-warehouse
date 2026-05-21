param(
    [string]$InstallDir = "$env:ProgramData\RTResearchWarehouse"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $InstallDir "docker-compose.yml"))) {
    throw "Application is not installed at $InstallDir"
}

Push-Location $InstallDir
try {
    docker compose -f docker-compose.yml -f docker-compose.installer.yml --env-file .env up -d postgres orthanc api web
    Start-Process "http://localhost:8080"
    Write-Host "RT Research Warehouse started: http://localhost:8080" -ForegroundColor Green
} finally {
    Pop-Location
}
