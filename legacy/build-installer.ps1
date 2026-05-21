param(
    [string]$InnoCompiler = "",
    [switch]$SkipStaging,
    [switch]$SkipWebBuild
)

$ErrorActionPreference = "Stop"

function Invoke-Native {
    param([string]$FilePath, [string[]]$Arguments)
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Find-InnoCompiler {
    param([string]$ExplicitPath)
    if ($ExplicitPath) {
        if (Test-Path $ExplicitPath) { return (Resolve-Path $ExplicitPath).Path }
        throw "Inno Setup compiler not found: $ExplicitPath"
    }

    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }
    throw "Cannot find ISCC.exe. Install Inno Setup 6.3.x or pass -InnoCompiler."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not $SkipStaging) {
    $stagingArgs = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $repoRoot "legacy\build-legacy-package.ps1"))
    if ($SkipWebBuild) { $stagingArgs += "-SkipWebBuild" }
    Invoke-Native "powershell" $stagingArgs
}

$iscc = Find-InnoCompiler $InnoCompiler
$iss = Join-Path $repoRoot "legacy\installer\RTResearchWarehouseLegacy.iss"
Invoke-Native $iscc @($iss)

Write-Host "Installer build finished. See legacy\output." -ForegroundColor Green
