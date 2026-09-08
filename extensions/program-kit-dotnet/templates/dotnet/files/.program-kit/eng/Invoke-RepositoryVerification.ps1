[CmdletBinding()]
param(
    [ValidateSet('CI', 'Release')]
    [string]$Mode = 'CI'
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$consumerPath = Join-Path $repository 'eng\verify.ps1'

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

$buildingBlockSelection = Join-Path $repository 'docs\architecture\building-block-selection.json'
if (Test-Path -LiteralPath $buildingBlockSelection -PathType Leaf) {
    $buildingBlockResolver = Join-Path $repository '.specify\extensions\program-kit-building-blocks\scripts\building_blocks.py'
    if (-not (Test-Path -LiteralPath $buildingBlockResolver -PathType Leaf)) {
        throw 'Accepted building-block selection exists but its installed resolver is missing.'
    }
    & python $buildingBlockResolver check --target $repository
    if ($LASTEXITCODE -ne 0) {
        throw "Managed $Mode verification rejected stale building-block selection or materialization."
    }
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
        return
    }
    throw 'Consumer verification must be a regular repository file, not a directory or reparse point.'
}

& (Join-Path $PSScriptRoot 'Build.ps1') -SkipRunnableHost -LockedMode
if (-not $?) {
    throw "Managed $Mode verification fallback failed."
}
