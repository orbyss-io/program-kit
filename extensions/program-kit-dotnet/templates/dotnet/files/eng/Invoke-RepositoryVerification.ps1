[CmdletBinding()]
param(
    [ValidateSet('CI', 'Release')]
    [string]$Mode = 'CI'
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$consumerPath = Join-Path $repository 'eng\verify.ps1'

function Invoke-ArchitectureChecks {
    & python (Join-Path $PSScriptRoot 'repository_architecture.py') --repository $repository `
        --manifest eng/architecture.json --configuration Release --output artifacts/tests/architecture.xml
    if ($LASTEXITCODE -ne 0) { throw 'Application architecture checks failed. See artifacts/tests/architecture.xml.' }
}

function Test-ProgramKitPathWithinRoot {
    param(
        [Parameter(Mandatory)] [string]$RootPath,
        [Parameter(Mandatory)] [string]$CandidatePath
    )

    $rootPrefix = [System.IO.Path]::GetFullPath($RootPath)
    $separator = [System.IO.Path]::DirectorySeparatorChar.ToString()
    if (-not $rootPrefix.EndsWith($separator)) {
        $rootPrefix += $separator
    }
    $candidateFullPath = [System.IO.Path]::GetFullPath($CandidatePath)
    $comparison = if ($env:OS -eq 'Windows_NT') {
        [System.StringComparison]::OrdinalIgnoreCase
    }
    else {
        [System.StringComparison]::Ordinal
    }
    return $candidateFullPath.StartsWith($rootPrefix, $comparison)
}

& (Join-Path $PSScriptRoot 'Restore.ps1') -EnvironmentOnly
if (-not $?) {
    throw "Managed $Mode verification could not prepare the repository-owned NuGet/.NET environment."
}

if (Test-Path -LiteralPath $consumerPath) {
    $consumer = Get-Item -LiteralPath $consumerPath -Force
    if (-not $consumer.PSIsContainer -and ($consumer.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) {
        $resolved = (Resolve-Path -LiteralPath $consumer.FullName).Path
        if (-not (Test-ProgramKitPathWithinRoot -RootPath $repository -CandidatePath $resolved)) {
            throw 'Consumer verification must resolve inside the repository.'
        }
        & $resolved
        if (-not $?) {
            throw 'Consumer verification failed.'
        }
        Invoke-ArchitectureChecks
        return
    }
    throw 'Consumer verification must be a regular repository file, not a directory or reparse point.'
}

& (Join-Path $PSScriptRoot 'Build.ps1') -SkipReleaseBundle -LockedMode
if (-not $?) {
    throw "Managed $Mode verification fallback failed."
}
Invoke-ArchitectureChecks
