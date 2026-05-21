param(
    [string]$WheelhouseRoot = "legacy\wheelhouse",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

function Invoke-Native {
    param([string]$FilePath, [string[]]$Arguments)
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$wheelhouse = Join-Path $repoRoot $WheelhouseRoot
$requirements = Join-Path $repoRoot "legacy\requirements-py38.txt"

New-Item -ItemType Directory -Force $wheelhouse | Out-Null

Invoke-Native $Python @(
    "-m", "pip", "download",
    "--dest", $wheelhouse,
    "--platform", "win_amd64",
    "--python-version", "38",
    "--implementation", "cp",
    "--abi", "cp38",
    "--only-binary=:all:",
    "-r", $requirements
)

Write-Host "Wheelhouse downloaded to $wheelhouse" -ForegroundColor Green
