param(
    [string]$VendorRoot = "legacy\vendor"
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Download-File {
    param([string]$Url, [string]$Destination)
    if (Test-Path $Destination) {
        Write-Host "Exists: $Destination"
        return $true
    }
    Write-Host "Downloading $Url"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $client = New-Object System.Net.WebClient
        try {
            $client.DownloadFile($Url, $Destination)
            return $true
        } catch {
            if (Test-Path $Destination) {
                Remove-Item -Force $Destination
            }
            Write-Warning "Attempt $attempt failed: $($_.Exception.Message)"
            Start-Sleep -Seconds (2 * $attempt)
        } finally {
            $client.Dispose()
        }
    }
    return $false
}

function Write-Checksums {
    param([string]$Root)
    $manifest = Join-Path $Root "SHA256SUMS.txt"
    $lines = @()
    Get-ChildItem -LiteralPath $Root -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" -and $_.Name -ne "README.md" } | Sort-Object Name | ForEach-Object {
        $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName
        $lines += "$($hash.Hash)  $($_.Name)"
    }
    $lines | Set-Content -Path $manifest -Encoding ASCII
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$vendor = Join-Path $repoRoot $VendorRoot
New-Item -ItemType Directory -Force $vendor | Out-Null

$downloads = @(
    @{
        Name = "python-3.8.10-amd64.exe"
        Url = "https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe"
    },
    @{
        Name = "postgresql-10.23-1-windows-x64-binaries.zip"
        Url = "https://get.enterprisedb.com/postgresql/postgresql-10.23-1-windows-x64-binaries.zip"
    },
    @{
        Name = "Orthanc-1.11.3-Release.exe"
        Url = "https://orthanc.uclouvain.be/downloads/windows-32/orthanc/Orthanc-1.11.3-Release.exe"
    },
    @{
        Name = "nssm-2.24.zip"
        Url = "https://nssm.cc/release/nssm-2.24.zip"
    }
)

Write-Step "Downloading third-party vendor packages"
$failed = @()
foreach ($item in $downloads) {
    if ($item.Name -like "Orthanc-*") {
        $existingOrthanc = Get-ChildItem -LiteralPath $vendor -File | Where-Object { $_.Name -like "Orthanc*.exe" -or $_.Name -like "Orthanc*.zip" } | Select-Object -First 1
        if ($existingOrthanc) {
            Write-Host "Exists: $($existingOrthanc.FullName)"
            continue
        }
    }
    $ok = Download-File $item.Url (Join-Path $vendor $item.Name)
    if (-not $ok) {
        $failed += "$($item.Name) <= $($item.Url)"
    }
}

Write-Step "Writing SHA256 manifest"
Write-Checksums $vendor

Write-Host ""
Write-Host "Vendor packages downloaded to $vendor" -ForegroundColor Green
if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Warning "Some vendor packages could not be downloaded automatically:"
    $failed | ForEach-Object { Write-Warning $_ }
    throw "Download incomplete. Place missing files under $vendor and rerun this script."
}
