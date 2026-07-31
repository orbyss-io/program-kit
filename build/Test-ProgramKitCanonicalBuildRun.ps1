[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string] $RunMetadataPath,
    [Parameter(Mandatory = $true)][string] $ArtifactMetadataPath,
    [Parameter(Mandatory = $true)][string] $Repository,
    [Parameter(Mandatory = $true)][string] $RunId,
    [Parameter(Mandatory = $true)][string] $WorkflowIdentity
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RequiredProperty {
    param(
        [Parameter(Mandatory = $true)][psobject] $Value,
        [Parameter(Mandatory = $true)][string] $Name,
        [Parameter(Mandatory = $true)][string] $Path
    )

    $property = $Value.PSObject.Properties[$Name]
    if ($null -eq $property -or $null -eq $property.Value) {
        throw "Required GitHub metadata is absent at $Path/$Name."
    }

    return $property.Value
}

function Assert-PositiveInteger {
    param(
        [Parameter(Mandatory = $true)][string] $Value,
        [Parameter(Mandatory = $true)][string] $Path
    )

    if ($Value -cnotmatch '^[1-9][0-9]*$') {
        throw "Expected a positive integer at ${Path}: $Value"
    }
}

if (-not (Test-Path -LiteralPath $RunMetadataPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $ArtifactMetadataPath -PathType Leaf)) {
    throw 'The selected run or artifact metadata file is absent.'
}

if ($Repository -cnotmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' -or
    $WorkflowIdentity -cnotmatch '^\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml$') {
    throw 'The expected repository or workflow identity is invalid.'
}

Assert-PositiveInteger -Value $RunId -Path '/expected/runId'
$run = Get-Content -Raw -LiteralPath $RunMetadataPath | ConvertFrom-Json
$actualRunId = [string] (
    Get-RequiredProperty -Value $run -Name 'id' -Path '/run')
Assert-PositiveInteger -Value $actualRunId -Path '/run/id'
$runRepository = Get-RequiredProperty `
    -Value $run `
    -Name 'repository' `
    -Path '/run'
$headRepository = Get-RequiredProperty `
    -Value $run `
    -Name 'head_repository' `
    -Path '/run'
$sourceCommit = [string] (
    Get-RequiredProperty -Value $run -Name 'head_sha' -Path '/run')
$runAttempt = [string] (
    Get-RequiredProperty -Value $run -Name 'run_attempt' -Path '/run')
Assert-PositiveInteger -Value $runAttempt -Path '/run/run_attempt'
if ($actualRunId -cne $RunId -or
    [string] (
        Get-RequiredProperty `
            -Value $runRepository `
            -Name 'full_name' `
            -Path '/run/repository') -cne $Repository -or
    [string] (
        Get-RequiredProperty `
            -Value $headRepository `
            -Name 'full_name' `
            -Path '/run/head_repository') -cne $Repository -or
    [string] (
        Get-RequiredProperty -Value $run -Name 'event' -Path '/run') -cne
            'push' -or
    [string] (
        Get-RequiredProperty `
            -Value $run `
            -Name 'head_branch' `
            -Path '/run') -cne 'main' -or
    [string] (
        Get-RequiredProperty -Value $run -Name 'status' -Path '/run') -cne
            'completed' -or
    [string] (
        Get-RequiredProperty `
            -Value $run `
            -Name 'conclusion' `
            -Path '/run') -cne 'success' -or
    [string] (
        Get-RequiredProperty -Value $run -Name 'path' -Path '/run') -cne
            $WorkflowIdentity -or
    $sourceCommit -cnotmatch '^[0-9a-f]{40}$') {
    throw 'The selected run is not an eligible successful main-push canonical build.'
}

$artifactResponse = Get-Content `
    -Raw `
    -LiteralPath $ArtifactMetadataPath |
    ConvertFrom-Json
$reportedCount = [int] (
    Get-RequiredProperty `
        -Value $artifactResponse `
        -Name 'total_count' `
        -Path '/artifacts')
$artifacts = @(
    Get-RequiredProperty `
        -Value $artifactResponse `
        -Name 'artifacts' `
        -Path '/artifacts')
if ($reportedCount -ne 1 -or $artifacts.Count -ne 1) {
    throw 'The selected run must have exactly one canonical-build artifact.'
}

$artifact = $artifacts[0]
$artifactId = [string] (
    Get-RequiredProperty -Value $artifact -Name 'id' -Path '/artifact')
Assert-PositiveInteger -Value $artifactId -Path '/artifact/id'
$artifactName = [string] (
    Get-RequiredProperty -Value $artifact -Name 'name' -Path '/artifact')
$artifactDigest = [string] (
    Get-RequiredProperty -Value $artifact -Name 'digest' -Path '/artifact')
$artifactSize = [string] (
    Get-RequiredProperty `
        -Value $artifact `
        -Name 'size_in_bytes' `
        -Path '/artifact')
Assert-PositiveInteger -Value $artifactSize -Path '/artifact/size_in_bytes'
$artifactRun = Get-RequiredProperty `
    -Value $artifact `
    -Name 'workflow_run' `
    -Path '/artifact'
$expired = Get-RequiredProperty `
    -Value $artifact `
    -Name 'expired' `
    -Path '/artifact'
$expectedArtifactName = "program-kit-canonical-build-$sourceCommit"
if ($artifactName -cne $expectedArtifactName -or
    $artifactDigest -cnotmatch '^sha256:[0-9a-f]{64}$' -or
    [bool] $expired -or
    [string] (
        Get-RequiredProperty `
            -Value $artifactRun `
            -Name 'id' `
            -Path '/artifact/workflow_run') -cne $RunId -or
    [string] (
        Get-RequiredProperty `
            -Value $artifactRun `
            -Name 'head_branch' `
            -Path '/artifact/workflow_run') -cne 'main' -or
    [string] (
        Get-RequiredProperty `
            -Value $artifactRun `
            -Name 'head_sha' `
            -Path '/artifact/workflow_run') -cne $sourceCommit) {
    throw 'The selected hosted artifact does not belong to the eligible canonical build.'
}

$selection = [ordered]@{
    runId = $RunId
    runAttempt = $runAttempt
    sourceCommit = $sourceCommit
    workflowIdentity = $WorkflowIdentity
    workflowRevision = $sourceCommit
    artifactId = $artifactId
    artifactName = $artifactName
    artifactDigest = $artifactDigest
    artifactSize = [long] $artifactSize
}
$selection | ConvertTo-Json -Depth 4 -Compress
