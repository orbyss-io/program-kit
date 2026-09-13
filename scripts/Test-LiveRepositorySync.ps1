[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('feature-intake', 'feature-planning', 'feature-plan-tasks', 'feature-setup', 'feature-delivery', 'upgrade-consumer', 'upgrade-continuation')]
    [string]$Phase,
    [Parameter(Mandatory)]
    [ValidateSet('fresh-baseline', 'fresh-candidate', 'upgrade-candidate')]
    [string]$Case,
    [Parameter(Mandatory)][string]$Authorization,
    [Parameter(Mandatory)][string]$Checkpoint
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
& python (Join-Path $projectRoot 'tests/live/v2/cli.py') sync-stage --phase $Phase --case $Case `
    --authorization (Resolve-Path -LiteralPath $Authorization).Path --checkpoint (Resolve-Path -LiteralPath $Checkpoint).Path
if ($LASTEXITCODE -ne 0) { throw "Live repository sync phase failed with exit code $LASTEXITCODE. Inspect preserved evidence; reruns need a new one-use authorization." }
