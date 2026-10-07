[CmdletBinding()]
param(
    [ValidateSet('CI', 'Release')]
    [string]$Mode = 'CI',
    [ValidateSet('Acceptance', 'Focused', 'Affected')]
    [string]$Scope = 'Acceptance',
    [string[]]$Projects = @(),
    [string[]]$TestArguments = @(),
    [string[]]$ChangedPaths = @(),
    [string]$ChangedFrom = '',
    [string]$FeatureDirectory = '',
    [string]$Configuration = 'Debug',
    [switch]$Restore,
    [switch]$Plan
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

function Resolve-ConsumerVerification {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Consumer verification must be a regular repository file, not a directory or reparse point.'
    }
    $resolved = (Resolve-Path -LiteralPath $item.FullName).Path
    if (-not (Test-ProgramKitPathWithinRoot -RootPath $repository -CandidatePath $resolved)) {
        throw 'Consumer verification must resolve inside the repository.'
    }
    return $resolved
}

if ($Scope -ne 'Acceptance') {
    if ($Mode -eq 'Release') { throw 'PKV002 scoped development checks cannot claim Release acceptance.' }
    $scopedPath = Join-Path $repository 'eng\verify-scoped.ps1'
    if (Test-Path -LiteralPath $scopedPath) {
        $resolved = Resolve-ConsumerVerification $scopedPath
        & $resolved -Scope $Scope -Projects $Projects -TestArguments $TestArguments `
            -ChangedPaths $ChangedPaths -ChangedFrom $ChangedFrom -FeatureDirectory $FeatureDirectory `
            -Configuration $Configuration -Restore:$Restore -Plan:$Plan
        if (-not $?) { throw 'Scoped consumer verification failed.' }
    }
    else {
        $arguments = @((Join-Path $PSScriptRoot 'repository_verification.py'), '--repository', $repository,
            '--scope', $Scope, '--configuration', $Configuration)
        foreach ($project in $Projects) { $arguments += @('--project', $project) }
        foreach ($path in $ChangedPaths) { $arguments += @('--changed-path', $path) }
        foreach ($argument in $TestArguments) { $arguments += "--test-argument=$argument" }
        if ($ChangedFrom) { $arguments += @('--changed-from', $ChangedFrom) }
        if ($FeatureDirectory) { $arguments += @('--feature-dir', $FeatureDirectory) }
        if ($Restore) { $arguments += '--restore' }
        if ($Plan) { $arguments += '--plan' }
        if (-not $Plan) {
            & (Join-Path $PSScriptRoot 'Restore.ps1') -EnvironmentOnly
            if (-not $?) { throw 'Could not prepare the native development environment.' }
        }
        & python @arguments
        if ($LASTEXITCODE -ne 0) { throw 'Scoped native checks failed. No full-suite fallback was executed.' }
    }
    Write-Host "Scoped $Scope checks completed; full application acceptance is not established."
    return
}
if ($Projects.Count -or $TestArguments.Count -or $ChangedPaths.Count -or $ChangedFrom -or $Plan -or $Restore) {
    throw 'PKV002 Acceptance cannot be narrowed by development selection parameters.'
}

& (Join-Path $PSScriptRoot 'Restore.ps1') -EnvironmentOnly
if (-not $?) {
    throw "Managed $Mode verification could not prepare the repository-owned NuGet/.NET environment."
}

if (Test-Path -LiteralPath $consumerPath) {
    $resolved = Resolve-ConsumerVerification $consumerPath
    & $resolved
    if (-not $?) {
        throw 'Consumer verification failed.'
    }
    Invoke-ArchitectureChecks
    return
}

& (Join-Path $PSScriptRoot 'Build.ps1') -SkipReleaseBundle -LockedMode -VerifyArchitecture
if (-not $?) {
    throw "Managed $Mode verification fallback failed."
}
