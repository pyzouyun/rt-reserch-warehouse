. "$PSScriptRoot\common.ps1"

$root = Get-LegacyRoot
$envValues = Read-EnvFile (Join-Path $root "config\.env")
Set-ProcessEnvironment $envValues
Set-Location $root
& (Join-Path $root "runtime\python38\python.exe") -m etl.run_etl
exit $LASTEXITCODE
