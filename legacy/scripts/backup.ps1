. "$PSScriptRoot\common.ps1"

$root = Get-LegacyRoot
$envValues = Read-EnvFile (Join-Path $root "config\.env")
$backupDir = Join-Path $root ("backup\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force $backupDir | Out-Null

$pgDump = Join-Path $root "runtime\postgres\bin\pg_dump.exe"
$env:PGPASSWORD = $envValues["POSTGRES_PASSWORD"]
Invoke-Native $pgDump @("-h", "127.0.0.1", "-p", $envValues["POSTGRES_PORT"], "-U", $envValues["POSTGRES_USER"], "-d", $envValues["POSTGRES_DB"], "-f", (Join-Path $backupDir "rt_research.sql"))
Copy-Item -Recurse -Force (Join-Path $root "data\orthanc") (Join-Path $backupDir "orthanc")
Copy-Item -Force (Join-Path $root "config\.env") (Join-Path $backupDir ".env")

Write-Host "Backup written to $backupDir" -ForegroundColor Green
