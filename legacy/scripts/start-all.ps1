. "$PSScriptRoot\common.ps1"

Start-Service RTResearch-PostgreSQL
Start-Service RTResearch-Orthanc
Start-Service RTResearch-API
Start-Process "http://localhost:8080"
Write-Host "RT Research legacy services started." -ForegroundColor Green
