param(
    [string]$InstallDir = "$env:ProgramData\RTResearchWarehouse",
    [switch]$RemoveData
)

$ErrorActionPreference = "Stop"

if (Test-Path (Join-Path $InstallDir "docker-compose.yml")) {
    Push-Location $InstallDir
    try {
        if ($RemoveData) {
            docker compose -f docker-compose.yml -f docker-compose.installer.yml --env-file .env down -v
        } else {
            docker compose -f docker-compose.yml -f docker-compose.installer.yml --env-file .env down
        }
    } finally {
        Pop-Location
    }
}

Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
Remove-Item -Force (Join-Path ([Environment]::GetFolderPath("Desktop")) "RT Research Warehouse - Start.lnk") -ErrorAction SilentlyContinue
Remove-Item -Force (Join-Path ([Environment]::GetFolderPath("Desktop")) "RT Research Warehouse - Stop.lnk") -ErrorAction SilentlyContinue

Write-Host "RT Research Warehouse uninstalled." -ForegroundColor Green
if (-not $RemoveData) {
    Write-Host "Docker volumes were kept. Rerun with -RemoveData to delete database and Orthanc data."
}
