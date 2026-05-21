param(
    [string]$VendorRoot = "legacy\vendor",
    [string]$RuntimeRoot = "legacy\runtime",
    [string]$WheelhouseRoot = "legacy\wheelhouse",
    [switch]$AllowOnlinePip
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Copy-DirectoryContents {
    param([string]$Source, [string]$Destination)
    if (Test-Path $Destination) {
        Remove-Item -Recurse -Force $Destination
    }
    New-Item -ItemType Directory -Force $Destination | Out-Null
    Copy-Item -Recurse -Force (Join-Path $Source "*") $Destination
}

function Expand-ZipToTemp {
    param([string]$ZipPath)
    $tempRoot = Join-Path $env:SystemDrive "rtwtmp"
    New-Item -ItemType Directory -Force $tempRoot | Out-Null
    $temp = Join-Path $tempRoot ([Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force $temp | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        foreach ($entry in $zip.Entries) {
            $relative = $entry.FullName.Replace("/", "\")
            if ($relative -match "\\pgAdmin 4\\") {
                continue
            }
            if (-not $entry.Name) {
                continue
            }
            $destination = Join-Path $temp $relative
            $destinationDir = Split-Path $destination -Parent
            New-Item -ItemType Directory -Force $destinationDir | Out-Null
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $destination, $true)
        }
    } finally {
        $zip.Dispose()
    }
    return $temp
}

function Find-FirstFile {
    param([string]$Root, [string]$Filter)
    $file = Get-ChildItem -LiteralPath $Root -Recurse -Filter $Filter | Select-Object -First 1
    if ($file) {
        return $file.FullName
    }
    return $null
}

function Invoke-Native {
    param([string]$FilePath, [string[]]$Arguments)
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Copy-OrthancInstalledRuntime {
    param([string]$Destination)
    $candidates = @(
        (Join-Path $env:ProgramFiles "Orthanc Server"),
        (Join-Path ${env:ProgramFiles(x86)} "Orthanc Server")
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path (Join-Path $candidate "Orthanc.exe"))) {
            Copy-DirectoryContents $candidate $Destination
            return $true
        }
    }
    return $false
}

function Uninstall-TemporaryOrthanc {
    $service = Get-Service Orthanc -ErrorAction SilentlyContinue
    if ($service) {
        Stop-Service Orthanc -Force -ErrorAction SilentlyContinue
    }
    $uninstallers = @(
        (Join-Path $env:ProgramFiles "Orthanc Server\unins000.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Orthanc Server\unins000.exe")
    )
    foreach ($uninstaller in $uninstallers) {
        if ($uninstaller -and (Test-Path $uninstaller)) {
            Invoke-Native $uninstaller @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
            return
        }
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$vendor = Join-Path $repoRoot $VendorRoot
$runtime = Join-Path $repoRoot $RuntimeRoot
$wheelhouse = Join-Path $repoRoot $WheelhouseRoot

New-Item -ItemType Directory -Force $vendor | Out-Null
New-Item -ItemType Directory -Force $runtime | Out-Null

Write-Step "Preparing Python 3.8 runtime"
$pythonDir = Join-Path $runtime "python38"
$pythonExe = Join-Path $pythonDir "python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonInstaller = Find-FirstFile $vendor "python-3.8.10-amd64.exe"
    if (-not $pythonInstaller) {
        throw "Missing Python installer. Put python-3.8.10-amd64.exe under $vendor, or preinstall Python into $pythonDir."
    }
    New-Item -ItemType Directory -Force $pythonDir | Out-Null
    Invoke-Native $pythonInstaller @(
        "/quiet",
        "InstallAllUsers=0",
        "TargetDir=$pythonDir",
        "Include_pip=1",
        "Include_launcher=0",
        "InstallLauncherAllUsers=0",
        "PrependPath=0",
        "Shortcuts=0",
        "Include_doc=0",
        "Include_test=0"
    )
}

Write-Step "Installing Python dependencies"
$requirements = Join-Path $repoRoot "legacy\requirements-py38.txt"
& $pythonExe -m pip --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    Invoke-Native $pythonExe @("-m", "ensurepip", "--upgrade")
}
if (Test-Path $wheelhouse) {
    Invoke-Native $pythonExe @("-m", "pip", "install", "--no-index", "--find-links", $wheelhouse, "-r", $requirements)
} elseif ($AllowOnlinePip) {
    Invoke-Native $pythonExe @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-Native $pythonExe @("-m", "pip", "install", "-r", $requirements)
} else {
    throw "Missing $wheelhouse. Create an offline wheelhouse first, or rerun with -AllowOnlinePip on the build machine."
}

Write-Step "Preparing PostgreSQL runtime"
$postgresDir = Join-Path $runtime "postgres"
if (-not (Test-Path (Join-Path $postgresDir "bin\postgres.exe"))) {
    $postgresZip = Find-FirstFile $vendor "postgresql-10.23-*-windows-x64-binaries.zip"
    if (-not $postgresZip) {
        throw "Missing PostgreSQL binaries zip under $vendor."
    }
    $temp = Expand-ZipToTemp $postgresZip
    try {
        $postgresExe = Find-FirstFile $temp "postgres.exe"
        if (-not $postgresExe) { throw "Cannot find postgres.exe in $postgresZip" }
        $binDir = Split-Path $postgresExe -Parent
        $sourceRoot = Split-Path $binDir -Parent
        Copy-DirectoryContents $sourceRoot $postgresDir
    } finally {
        Remove-Item -Recurse -Force $temp
    }
}

Write-Step "Preparing NSSM runtime"
$nssmDir = Join-Path $runtime "nssm"
if (-not (Test-Path (Join-Path $nssmDir "win64\nssm.exe")) -and -not (Test-Path (Join-Path $nssmDir "nssm.exe"))) {
    $nssmZip = Find-FirstFile $vendor "nssm-*.zip"
    if (-not $nssmZip) {
        throw "Missing NSSM zip under $vendor."
    }
    $temp = Expand-ZipToTemp $nssmZip
    try {
        $nssmExe = Find-FirstFile $temp "nssm.exe"
        if (-not $nssmExe) { throw "Cannot find nssm.exe in $nssmZip" }
        $sourceRoot = Split-Path (Split-Path $nssmExe -Parent) -Parent
        Copy-DirectoryContents $sourceRoot $nssmDir
    } finally {
        Remove-Item -Recurse -Force $temp
    }
}

Write-Step "Preparing Orthanc runtime"
$orthancDir = Join-Path $runtime "orthanc"
if (-not (Test-Path (Join-Path $orthancDir "Orthanc.exe"))) {
    $orthancZip = Find-FirstFile $vendor "Orthanc-*.zip"
    if ($orthancZip) {
        $temp = Expand-ZipToTemp $orthancZip
        try {
            $orthancExe = Find-FirstFile $temp "Orthanc.exe"
            if (-not $orthancExe) { throw "Cannot find Orthanc.exe in $orthancZip" }
            Copy-DirectoryContents (Split-Path $orthancExe -Parent) $orthancDir
        } finally {
            Remove-Item -Recurse -Force $temp
        }
    } else {
        $orthancExe = Find-FirstFile $vendor "Orthanc.exe"
        if ($orthancExe) {
            Copy-DirectoryContents (Split-Path $orthancExe -Parent) $orthancDir
        } else {
            $orthancInstaller = Find-FirstFile $vendor "Orthanc-*-Release.exe"
            if (-not $orthancInstaller) {
                $orthancInstaller = Find-FirstFile $vendor "OrthancInstaller-*.exe"
            }
            if (-not $orthancInstaller) {
                throw "Missing Orthanc runtime. Put an unpacked Orthanc.exe folder, Orthanc-*.zip, Orthanc-*-Release.exe, or OrthancInstaller-*.exe under $vendor."
            }
            New-Item -ItemType Directory -Force $orthancDir | Out-Null
            Invoke-Native $orthancInstaller @("/S")
            if (-not (Test-Path (Join-Path $orthancDir "Orthanc.exe"))) {
                $copied = Copy-OrthancInstalledRuntime $orthancDir
                Uninstall-TemporaryOrthanc
                if (-not $copied) {
                    throw "Orthanc installer finished but Orthanc.exe was not found. Install it manually and rerun."
                }
            }
            if (-not (Test-Path (Join-Path $orthancDir "Orthanc.exe"))) {
                throw "Orthanc installer finished but Orthanc.exe was not found in $orthancDir. Install it manually and rerun."
            }
        }
    }
}

Write-Host ""
Write-Host "Legacy runtime prepared under $runtime" -ForegroundColor Green
