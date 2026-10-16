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
    [string]$Reason = '',
    [switch]$Force,
    [switch]$Restore,
    [switch]$Plan
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$consumerPath = Join-Path $repository 'eng\verify.ps1'

function Resolve-VerificationPython {
    $recordPath = Join-Path $repository '.specify/python-runtime.json'
    $saved = $null
    try {
        if (Test-Path -LiteralPath $recordPath) {
            $saved = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
            if ($saved.contractVersion -ne 1 -or -not $saved.executable) { throw 'Unsupported core runtime record.' }
        }
        $executable = $env:SPECKIT_PYTHON
        if (-not $executable -and $saved) { $executable = $saved.executable }
        if (-not $executable) {
            $command = Get-Command python -ErrorAction SilentlyContinue
            if ($command) { $executable = $command.Source }
        }
        if (-not $executable -or -not [IO.Path]::IsPathRooted($executable) -or
            -not (Test-Path -LiteralPath $executable -PathType Leaf)) { throw 'Selected interpreter is absent or not an absolute file.' }
        if ($saved -and [IO.Path]::GetFullPath($executable) -ne [IO.Path]::GetFullPath($saved.executable)) {
            throw 'SPECKIT_PYTHON differs from the core runtime record; regenerate core instructions explicitly.'
        }
        $probe = 'import json,sys; print(json.dumps({''executable'':sys.executable,''version'':''.''.join(map(str,sys.version_info[:3])),''supported'':sys.version_info>=(3,11)}))'
        $output = & $executable -c $probe
        if ($LASTEXITCODE -ne 0) { throw 'Selected interpreter did not execute the version probe.' }
        $actual = $output | ConvertFrom-Json
        if (-not $actual.supported) { throw 'Python >=3.11 is required.' }
        $pin = Join-Path $repository '.python-version'
        if ((Test-Path -LiteralPath $pin) -and $actual.version -ne (Get-Content -LiteralPath $pin -Raw).Trim()) {
            throw "Interpreter version $($actual.version) differs from .python-version."
        }
        return [IO.Path]::GetFullPath($actual.executable)
    }
    catch {
        throw "PKV005 verification Python is unavailable or stale. Select an installed absolute SPECKIT_PYTHON matching .specify/python-runtime.json, or regenerate core instructions after a reviewed runtime change. Verify the actual executable and .python-version in your terminal; no interpreter was installed and PATH was not changed. $($_.Exception.Message)"
    }
}

function Invoke-ArchitectureChecks {
    & $verificationPython (Join-Path $PSScriptRoot 'repository_architecture.py') --repository $repository `
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
    catch { throw "PKV004 invalid provider isolation declaration in eng/verification.json. $($_.Exception.Message)" }
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
    catch { throw "PKV004 invalid eng/ProviderTestEnvironment.psm1; repair isolation before verification. $($_.Exception.Message)" }
}
elseif ($isolationRequired) {
    throw 'PKV004 required eng/ProviderTestEnvironment.psm1 is missing; restore the consumer isolation module before verification. No child was dispatched.'
}

$verificationAction = {
$verificationPython = Resolve-VerificationPython
if ($Scope -ne 'Acceptance') {
    if ($Mode -eq 'Release') { throw 'PKV002 scoped development checks cannot claim Release acceptance.' }
    $scopedPath = Join-Path $repository 'eng\verify-scoped.ps1'
    if (Test-Path -LiteralPath $scopedPath) {
        $resolved = Resolve-ConsumerVerification $scopedPath
        $additional = @{}
        if ($Reason) { $additional.Reason = $Reason }
        if ($Force) { $additional.Force = $true }
        & $resolved -Scope $Scope -Projects $Projects -TestArguments $TestArguments `
            -ChangedPaths $ChangedPaths -ChangedFrom $ChangedFrom -FeatureDirectory $FeatureDirectory `
            -Configuration $Configuration -Restore:$Restore -Plan:$Plan @additional
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
        if ($Reason) { $arguments += @('--reason', $Reason) }
        if ($Force) { $arguments += '--force' }
        if ($Restore) { $arguments += '--restore' }
        if ($Plan) { $arguments += '--plan' }
        & (Join-Path $PSScriptRoot 'Restore.ps1') -EnvironmentOnly
        if (-not $?) { throw 'Could not prepare the native development environment.' }
        & $verificationPython @arguments
        if ($LASTEXITCODE -ne 0) { throw 'Scoped native checks failed. No full-suite fallback was executed.' }
    }
    if (-not $Plan) {
        Write-Host "Scoped $Scope checks completed; full application acceptance is not established."
    }
    return
}
if ($Projects.Count -or $TestArguments.Count -or $ChangedPaths.Count -or $ChangedFrom -or $Plan -or $Restore -or $Reason -or $Force) {
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
if ($isolationCommand) {
    & $isolationCommand -Action $verificationAction
}
else {
    & $verificationAction
}
