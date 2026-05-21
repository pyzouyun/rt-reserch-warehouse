. "$PSScriptRoot\common.ps1"

$root = Get-LegacyRoot
$envValues = Read-EnvFile (Join-Path $root "config\.env")
$nssm = Get-NssmPath $root
$python = Join-Path $root "runtime\python38\python.exe"
$postgres = Join-Path $root "runtime\postgres\bin\postgres.exe"
$orthanc = Join-Path $root "runtime\orthanc\Orthanc.exe"

if (-not (Test-Path $python)) { throw "Cannot find Python runtime at $python" }
if (-not (Test-Path $postgres)) { throw "Cannot find PostgreSQL runtime at $postgres" }
if (-not (Test-Path $orthanc)) { throw "Cannot find Orthanc executable at $orthanc" }

Invoke-Native $nssm @("install", "RTResearch-PostgreSQL", $postgres, "-D", (Join-Path $root "data\postgres"))
Invoke-Native $nssm @("set", "RTResearch-PostgreSQL", "AppDirectory", (Join-Path $root "runtime\postgres\bin"))
Invoke-Native $nssm @("set", "RTResearch-PostgreSQL", "AppStdout", (Join-Path $root "logs\postgres-service.log"))
Invoke-Native $nssm @("set", "RTResearch-PostgreSQL", "AppStderr", (Join-Path $root "logs\postgres-service.err.log"))

Invoke-Native $nssm @("install", "RTResearch-Orthanc", $orthanc, (Join-Path $root "config\orthanc.json"))
Invoke-Native $nssm @("set", "RTResearch-Orthanc", "AppDirectory", (Join-Path $root "runtime\orthanc"))
Invoke-Native $nssm @("set", "RTResearch-Orthanc", "AppStdout", (Join-Path $root "logs\orthanc-service.log"))
Invoke-Native $nssm @("set", "RTResearch-Orthanc", "AppStderr", (Join-Path $root "logs\orthanc-service.err.log"))

Invoke-Native $nssm @("install", "RTResearch-API", $python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", $envValues["API_PORT"])
Invoke-Native $nssm @("set", "RTResearch-API", "AppDirectory", $root)
Invoke-Native $nssm @("set", "RTResearch-API", "AppEnvironmentExtra", "RT_RESEARCH_HOME=$root")
Invoke-Native $nssm @("set", "RTResearch-API", "AppStdout", (Join-Path $root "logs\api-service.log"))
Invoke-Native $nssm @("set", "RTResearch-API", "AppStderr", (Join-Path $root "logs\api-service.err.log"))

netsh advfirewall firewall add rule name="RT Research DICOM C-STORE 4242" dir=in action=allow protocol=TCP localport=4242 | Out-Null

Write-Host "Services installed." -ForegroundColor Green
