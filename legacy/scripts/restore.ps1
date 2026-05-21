param([Parameter(Mandatory=$true)][string]$BackupDir)

. "$PSScriptRoot\common.ps1"

$root = Get-LegacyRoot
$envValues = Read-EnvFile (Join-Path $root "config\.env")
$psql = Join-Path $root "runtime\postgres\bin\psql.exe"
$env:PGPASSWORD = $envValues["POSTGRES_PASSWORD"]

if (-not (Test-Path (Join-Path $BackupDir "rt_research.sql"))) {
    throw "Cannot find rt_research.sql in $BackupDir"
}

Invoke-Native $psql @("-h", "127.0.0.1", "-p", $envValues["POSTGRES_PORT"], "-U", $envValues["POSTGRES_USER"], "-d", $envValues["POSTGRES_DB"], "-f", (Join-Path $BackupDir "rt_research.sql"))
if (Test-Path (Join-Path $BackupDir "orthanc")) {
    Copy-Item -Recurse -Force (Join-Path $BackupDir "orthanc") (Join-Path $root "data\orthanc")
}

Write-Host "Restore completed." -ForegroundColor Green
