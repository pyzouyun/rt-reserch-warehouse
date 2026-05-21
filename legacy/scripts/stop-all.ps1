. "$PSScriptRoot\common.ps1"

Stop-Service RTResearch-API -ErrorAction SilentlyContinue
Stop-Service RTResearch-Orthanc -ErrorAction SilentlyContinue
Stop-Service RTResearch-PostgreSQL -ErrorAction SilentlyContinue
Write-Host "RT Research legacy services stopped." -ForegroundColor Green
