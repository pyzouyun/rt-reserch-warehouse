param(
    [string]$PackageName = "RTResearchWarehouse-Windows",
    [string]$OutputRoot = "dist",
    [switch]$SkipImageBuild
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Ensure-Image {
    param(
        [string]$Image,
        [string]$FallbackImage = ""
    )
    try {
        Invoke-Native "docker" @("pull", $Image)
    } catch {
        if ([string]::IsNullOrWhiteSpace($FallbackImage)) {
            throw
        }
        Write-Warning "Could not pull $Image. Trying fallback $FallbackImage and retagging it."
        Invoke-Native "docker" @("pull", $FallbackImage)
        Invoke-Native "docker" @("tag", $FallbackImage, $Image)
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$distRoot = Join-Path $repoRoot $OutputRoot
$packageDir = Join-Path $distRoot $PackageName
$appDir = Join-Path $packageDir "app"
$imagesDir = Join-Path $packageDir "images"
$imageTar = Join-Path $imagesDir "rt-research-images.tar"
$zipPath = Join-Path $distRoot "$PackageName.zip"

Write-Step "Checking Docker"
Invoke-Native "docker" @("version")

if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
New-Item -ItemType Directory -Force $appDir, $imagesDir | Out-Null

if (-not $SkipImageBuild) {
    Write-Step "Building local application images"
    Invoke-Native "docker" @("compose", "--env-file", ".env.example", "build", "etl", "api", "web")

    Write-Step "Pulling third-party runtime images"
    Ensure-Image "orthancteam/orthanc:24.12.3" "orthancteam/orthanc:latest"
    Ensure-Image "postgres:16-alpine"
    Ensure-Image "dpage/pgadmin4:8.14"
}

Write-Step "Saving Docker images"
$images = @(
    "rt-research/etl:0.2.0",
    "rt-research/api:0.2.0",
    "rt-research/web:0.2.0",
    "orthancteam/orthanc:24.12.3",
    "postgres:16-alpine",
    "dpage/pgadmin4:8.14"
)
Invoke-Native "docker" (@("save", "-o", $imageTar) + $images)

Write-Step "Copying project files"
$excludeDirs = @(
    ".git",
    "dist",
    "web\node_modules",
    "web\dist",
    ".pytest_cache"
)
$excludeFiles = @(
    ".env",
    "*.pyc",
    "*.log"
)

$robocopyArgs = @(
    $repoRoot,
    $appDir,
    "/E",
    "/XD"
) + ($excludeDirs | ForEach-Object { Join-Path $repoRoot $_ }) + @("/XF") + $excludeFiles + @("/NFL", "/NDL", "/NJH", "/NJS", "/NP")

robocopy @robocopyArgs | Out-Null
if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

Write-Step "Copying installer scripts"
Copy-Item -Force (Join-Path $PSScriptRoot "install.ps1") $packageDir
Copy-Item -Force (Join-Path $PSScriptRoot "start.ps1") $packageDir
Copy-Item -Force (Join-Path $PSScriptRoot "stop.ps1") $packageDir
Copy-Item -Force (Join-Path $PSScriptRoot "uninstall.ps1") $packageDir
Copy-Item -Force (Join-Path $PSScriptRoot "README-Windows.md") $packageDir

Write-Step "Creating zip package"
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}
Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "Package created:" -ForegroundColor Green
Write-Host $zipPath
Write-Host ""
Write-Host "Copy this zip to another Windows computer, unzip it, then run install.ps1 as Administrator."
