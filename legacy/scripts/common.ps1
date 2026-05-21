$ErrorActionPreference = "Stop"

function Get-LegacyRoot {
    if ($env:RT_RESEARCH_HOME) {
        return $env:RT_RESEARCH_HOME
    }
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Read-EnvFile {
    param([string]$Path)
    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }
    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }
        $parts = $line.Split("=", 2)
        $values[$parts[0]] = $parts[1]
    }
    return $values
}

function New-Secret {
    param([int]$Bytes = 24)
    $buffer = New-Object byte[] $Bytes
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($buffer)
    } finally {
        $rng.Dispose()
    }
    return [Convert]::ToBase64String($buffer).Replace("+", "A").Replace("/", "B").Replace("=", "")
}

function Set-ProcessEnvironment {
    param([hashtable]$Values)
    foreach ($key in $Values.Keys) {
        [Environment]::SetEnvironmentVariable($key, $Values[$key], "Process")
    }
}

function Get-NssmPath {
    param([string]$Root)
    $candidates = @(
        (Join-Path $Root "runtime\nssm\win64\nssm.exe"),
        (Join-Path $Root "runtime\nssm\nssm.exe"),
        (Join-Path $Root "runtime\nssm.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "Cannot find nssm.exe under runtime\nssm"
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
