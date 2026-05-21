. "$PSScriptRoot\common.ps1"

$root = Get-LegacyRoot
$configDir = Join-Path $root "config"
$envPath = Join-Path $configDir ".env"
$templatePath = Join-Path $configDir "legacy.env.example"

New-Item -ItemType Directory -Force $configDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $root "data\postgres") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $root "data\orthanc\storage") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $root "data\orthanc\index") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $root "logs") | Out-Null

if (-not (Test-Path $envPath)) {
    $postgresPassword = New-Secret
    $orthancPassword = New-Secret
    $salt = New-Secret -Bytes 32
    $content = [System.IO.File]::ReadAllText($templatePath)
    $content = $content.Replace("change-this-postgres-password", $postgresPassword)
    $content = $content.Replace("change-this-orthanc-password", $orthancPassword)
    $content = $content.Replace("replace-with-long-random-site-secret", $salt)
    $content | Set-Content -Path $envPath -Encoding UTF8
}

$envValues = Read-EnvFile $envPath
$orthancTemplate = [System.IO.File]::ReadAllText((Join-Path $configDir "orthanc.legacy.json.template"))
$orthancConfig = $orthancTemplate `
    -replace "\{\{ORTHANC_USERNAME\}\}", $envValues["ORTHANC_USERNAME"] `
    -replace "\{\{ORTHANC_PASSWORD\}\}", $envValues["ORTHANC_PASSWORD"] `
    -replace "\{\{INSTALL_DIR\}\}", ($root.Replace("\", "/"))
$orthancConfig | Set-Content -Path (Join-Path $configDir "orthanc.json") -Encoding UTF8

Write-Host "Legacy configuration initialized at $root" -ForegroundColor Green
