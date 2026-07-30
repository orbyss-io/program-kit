[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string] $CanonicalBuildRoot,
    [Parameter(Mandatory = $true)][string] $Repository,
    [Parameter(Mandatory = $true)][string] $Event,
    [Parameter(Mandatory = $true)][string] $Branch,
    [Parameter(Mandatory = $true)][string] $SourceCommit,
    [Parameter(Mandatory = $true)][string] $WorkflowIdentity,
    [Parameter(Mandatory = $true)][string] $WorkflowRevision,
    [Parameter(Mandatory = $true)][string] $RunId,
    [Parameter(Mandatory = $true)][string] $ArtifactName,
    [Parameter(Mandatory = $true)][string] $ProfileIdentity,
    [Parameter(Mandatory = $true)][string] $ProfileVersion,
    [Parameter(Mandatory = $true)][string] $ProfileSha256
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot '..'))
Import-Module `
    (Join-Path $PSScriptRoot 'ProgramKitCanonicalBuildProvenance.psm1') `
    -Force

Test-ProgramKitCanonicalBuildProvenance `
    -CanonicalBuildRoot $CanonicalBuildRoot `
    -RepositoryRoot $repositoryRoot `
    -Repository $Repository `
    -Event $Event `
    -Branch $Branch `
    -SourceCommit $SourceCommit `
    -WorkflowIdentity $WorkflowIdentity `
    -WorkflowRevision $WorkflowRevision `
    -RunId $RunId `
    -ArtifactName $ArtifactName `
    -ProfileIdentity $ProfileIdentity `
    -ProfileVersion $ProfileVersion `
    -ProfileSha256 $ProfileSha256
