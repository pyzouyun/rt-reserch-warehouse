. "$PSScriptRoot\common.ps1"

$root = Get-LegacyRoot
$envValues = Read-EnvFile (Join-Path $root "config\.env")
$pgRoot = Join-Path $root "runtime\postgres"
$dataDir = Join-Path $root "data\postgres"
$initdb = Join-Path $pgRoot "bin\initdb.exe"
$psql = Join-Path $pgRoot "bin\psql.exe"
$pgCtl = Join-Path $pgRoot "bin\pg_ctl.exe"

if (-not (Test-Path $initdb)) {
    throw "Cannot find PostgreSQL runtime at $pgRoot"
}

if (-not (Test-Path (Join-Path $dataDir "PG_VERSION"))) {
    Invoke-Native $initdb @("-D", $dataDir, "-U", "postgres", "-E", "UTF8", "--locale=C")
    Copy-Item -Force (Join-Path $root "config\pg_hba.conf") (Join-Path $dataDir "pg_hba.conf")
    Add-Content -Path (Join-Path $dataDir "postgresql.conf") -Value ([System.IO.File]::ReadAllText((Join-Path $root "config\postgresql.conf.append")))
}

Invoke-Native $pgCtl @("-D", $dataDir, "-l", (Join-Path $root "logs\postgres-init.log"), "start")
try {
    $roleCheck = & $psql -U postgres -h 127.0.0.1 -p $envValues["POSTGRES_PORT"] -tAc "SELECT 1 FROM pg_roles WHERE rolname='rt_research'"
    if ($roleCheck -ne "1") {
        & $psql -U postgres -h 127.0.0.1 -p $envValues["POSTGRES_PORT"] -c "CREATE ROLE rt_research LOGIN PASSWORD '$($envValues["POSTGRES_PASSWORD"])';"
    }
    $databaseCheck = & $psql -U postgres -h 127.0.0.1 -p $envValues["POSTGRES_PORT"] -tAc "SELECT 1 FROM pg_database WHERE datname='rt_research'"
    if ($databaseCheck -ne "1") {
        & $psql -U postgres -h 127.0.0.1 -p $envValues["POSTGRES_PORT"] -c "CREATE DATABASE rt_research OWNER rt_research;"
    }
    Invoke-Native $psql @("-U", "rt_research", "-h", "127.0.0.1", "-p", $envValues["POSTGRES_PORT"], "-d", "rt_research", "-f", (Join-Path $root "sql\001_init.sql"))
} finally {
    Invoke-Native $pgCtl @("-D", $dataDir, "stop", "-m", "fast")
}

Write-Host "PostgreSQL initialized." -ForegroundColor Green
