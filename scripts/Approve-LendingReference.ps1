[CmdletBinding()]
param([Parameter(Mandatory)][string]$Review, [Parameter(Mandatory)][string]$Output)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$reviewPath = (Resolve-Path -LiteralPath $Review).Path
$document = Get-Content -LiteralPath $reviewPath -Raw | ConvertFrom-Json
Write-Host 'Reference admission starts no agent and does not authorize a paid phase.'
Write-Host $document.acceptanceScope
Write-Host $document.governance.rule
Write-Host "Exact review: $reviewPath"
$required = "ADMIT $($document.reviewSha256)"
$answer = Read-Host "After reviewing the referenced evidence and declared gaps, type '$required'"
if ($answer -cne $required) { throw 'Reference admission was not confirmed.' }
& python (Join-Path $projectRoot 'tests/manage_lending_reference.py') admit --review $reviewPath `
    --output ([System.IO.Path]::GetFullPath($Output)) --review-sha256 $document.reviewSha256 `
    --confirmation-text $answer --confirmation-source 'Human-owned PowerShell reference review'
if ($LASTEXITCODE -ne 0) { throw 'Reference admission failed; inspect the diagnostic.' }
