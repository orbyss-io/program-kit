[CmdletBinding()]
param(
    [ValidateSet('CI', 'Release')]
    [string]$Mode = 'CI',
    [ValidateSet('Acceptance', 'Focused', 'Affected')]
    [string]$Scope = 'Acceptance',
    [string[]]$Projects = @(),
    [string[]]$Checks = @(),
    [string[]]$TestArguments = @(),
    [string[]]$ChangedPaths = @(),
    [string]$ChangedFrom = '',
    [string]$FeatureDirectory = '',
    [string]$Configuration = 'Debug',
    [string]$Reason = '',
    [switch]$Force,
    [switch]$Restore,
    [switch]$Plan
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$consumerPath = Join-Path $repository 'scripts/verify.ps1'

Import-Module (Join-Path $PSScriptRoot 'ProgramKitPython.psm1') -Force

function Invoke-ArchitectureChecks {
    & $verificationPython (Join-Path $PSScriptRoot 'repository_architecture.py') --repository $repository `
        --manifest config/program-kit/architecture.json --configuration Release --output artifacts/tests/architecture.xml
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

# The consumer declares its own credential names and offline mode in this fixed
# repository module. Required isolation is admitted before any child dispatch.
$providerEnvironmentModule = Join-Path $PSScriptRoot 'ProviderTestEnvironment.psm1'
$isolationRequired = $false
$verificationConfiguration = Join-Path $PSScriptRoot 'verification.json'
if (Test-Path -LiteralPath $verificationConfiguration) {
    try {
        $settings = Get-Content -LiteralPath $verificationConfiguration -Raw | ConvertFrom-Json
        if ($settings.providerIsolation) {
            if ($settings.providerIsolation.required -isnot [bool]) { throw 'providerIsolation.required must be a boolean.' }
            $isolationRequired = $settings.providerIsolation.required
        }
    }
    catch { throw "PKV004 invalid provider isolation declaration in config/program-kit/verification.json. $($_.Exception.Message)" }
}
$isolationCommand = $null
if (Test-Path -LiteralPath $providerEnvironmentModule) {
    try {
        $resolvedModule = Resolve-ConsumerVerification $providerEnvironmentModule
        $module = Import-Module -Name $resolvedModule -Force -PassThru -ErrorAction Stop
        $isolationCommand = $module.ExportedCommands['Invoke-WithOfflineProviderTestEnvironment']
        if (-not $isolationCommand -or -not $isolationCommand.Parameters.ContainsKey('Action') -or
            $isolationCommand.Parameters['Action'].ParameterType -ne [scriptblock]) {
            throw 'Export Invoke-WithOfflineProviderTestEnvironment with a scriptblock Action parameter.'
        }
    }
    catch { throw "PKV004 invalid scripts/ProviderTestEnvironment.psm1; repair isolation before verification. $($_.Exception.Message)" }
}
elseif ($isolationRequired) {
    throw 'PKV004 required scripts/ProviderTestEnvironment.psm1 is missing; restore the consumer isolation module before verification. No child was dispatched.'
}

$verificationAction = {
$verificationPython = Resolve-ProgramKitPython -Repository $repository
$env:SPECKIT_PYTHON = $verificationPython
if ($Scope -ne 'Acceptance') {
    if ($Mode -eq 'Release') { throw 'PKV002 scoped development checks cannot claim Release acceptance.' }
    $scopedPath = Join-Path $repository 'scripts/verify-scoped.ps1'
    if (Test-Path -LiteralPath $scopedPath) {
        $resolved = Resolve-ConsumerVerification $scopedPath
        $additional = @{}
        if ($Reason) { $additional.Reason = $Reason }
        if ($Force) { $additional.Force = $true }
        if ($Checks.Count) { $additional.Checks = $Checks }
        & $resolved -Scope $Scope -Projects $Projects -TestArguments $TestArguments `
            -ChangedPaths $ChangedPaths -ChangedFrom $ChangedFrom -FeatureDirectory $FeatureDirectory `
            -Configuration $Configuration -Restore:$Restore -Plan:$Plan @additional
        if (-not $?) { throw 'Scoped consumer verification failed.' }
    }
    else {
        $arguments = @((Join-Path $PSScriptRoot 'repository_verification.py'), '--repository', $repository,
            '--scope', $Scope, '--configuration', $Configuration)
        foreach ($project in $Projects) { $arguments += @('--project', $project) }
        foreach ($check in $Checks) { $arguments += @('--check', $check) }
        foreach ($path in $ChangedPaths) { $arguments += @('--changed-path', $path) }
        foreach ($argument in $TestArguments) { $arguments += "--test-argument=$argument" }
        if ($ChangedFrom) { $arguments += @('--changed-from', $ChangedFrom) }
        if ($FeatureDirectory) { $arguments += @('--feature-dir', $FeatureDirectory) }
        if ($Reason) { $arguments += @('--reason', $Reason) }
        if ($Force) { $arguments += '--force' }
        if ($Restore) { $arguments += '--restore' }
        if ($Plan) { $arguments += '--plan' }
        $typedSelection = & $verificationPython @arguments --select-only
        if ($LASTEXITCODE -ne 0) {
            $selectionDiagnostic = ($typedSelection -join "`n")
            if ($selectionDiagnostic.Length -gt 4096) { $selectionDiagnostic = $selectionDiagnostic.Substring(0, 4096) }
            throw "Typed verification ownership selection failed; no check was dispatched. $selectionDiagnostic"
        }
        $selectedOwners = ($typedSelection -join "`n") | ConvertFrom-Json
        if ($selectedOwners.projects.Count) {
            & (Join-Path $PSScriptRoot 'Restore.ps1') -EnvironmentOnly
            if (-not $?) { throw 'Could not prepare the native development environment.' }
        }
        & $verificationPython @arguments
        if ($LASTEXITCODE -ne 0) { throw 'Scoped native checks failed. No full-suite fallback was executed.' }
    }
    if (-not $Plan) {
        Write-Host "Scoped $Scope checks completed; full application acceptance is not established."
    }
    return
}
if ($Projects.Count -or $Checks.Count -or $TestArguments.Count -or $ChangedPaths.Count -or $ChangedFrom -or $Plan -or $Restore -or $Reason -or $Force) {
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
}
$previousPython = $env:SPECKIT_PYTHON
try {
if ($isolationCommand) {
    & $isolationCommand -Action $verificationAction
}
else {
    & $verificationAction
}

}
finally { $env:SPECKIT_PYTHON = $previousPython }
