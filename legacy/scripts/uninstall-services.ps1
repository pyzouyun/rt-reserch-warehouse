. "$PSScriptRoot\common.ps1"

$root = Get-LegacyRoot
$nssm = Get-NssmPath $root

foreach ($service in @("RTResearch-API", "RTResearch-Orthanc", "RTResearch-PostgreSQL")) {
    Stop-Service $service -ErrorAction SilentlyContinue
    & $nssm remove $service confirm
}

netsh advfirewall firewall delete rule name="RT Research DICOM C-STORE 4242" | Out-Null
Write-Host "Services removed." -ForegroundColor Green
