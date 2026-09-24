[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunManifest,
    [Parameter(Mandatory)][string]$ReviewSha256
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$manifestPath = (Resolve-Path -LiteralPath $RunManifest).Path
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$workspace = [IO.Path]::GetFullPath((Join-Path $projectRoot $manifest.workspace))
if (-not $workspace.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Workspace escapes the live repository.' }
$review = Join-Path $workspace '.program-kit/specification-intake/RM01/review.md'
Get-Content -LiteralPath $review | Write-Host
Write-Host "Review hash: $ReviewSha256"
$answer = Read-Host "After reviewing this feature brief, type 'CONFIRM $ReviewSha256' to confirm this exact review"
if ($answer -cne "CONFIRM $ReviewSha256") { throw 'No feature confirmation was recorded.' }
& python (Join-Path $projectRoot 'tests/live/v2/cli.py') confirm-sync-intake --run-manifest $manifestPath `
    --review-sha256 $ReviewSha256 --confirmation-text $answer --confirmation-source 'Human-owned Confirm-LiveFeatureIntake.ps1 terminal'
if ($LASTEXITCODE -ne 0) { throw "Feature confirmation failed with exit code $LASTEXITCODE." }
