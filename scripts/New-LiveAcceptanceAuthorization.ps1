[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('bootstrap-checkpoint', 'building-block-consumer')]
    [string]$Phase,
    [Parameter(Mandatory)]
    [string]$ReleaseReceipt,
    [string]$Checkpoint = '',
    [Parameter(Mandatory)]
    [string]$Model,
    [Parameter(Mandatory)]
    [string]$ReasoningEffort,
    [int]$TimeoutSeconds = 7200,
    [int]$ExpiresMinutes = 30,
    [string]$Scenario = '',
    [string]$Output = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$receiptPath = (Resolve-Path -LiteralPath $ReleaseReceipt).Path
if ($Phase -eq 'building-block-consumer' -and -not $Checkpoint) {
    throw 'LIVE_AUTHORIZATION_CHECKPOINT_REQUIRED: building-block-consumer authorization must bind a checkpoint.'
}
if ($Checkpoint) { $Checkpoint = (Resolve-Path -LiteralPath $Checkpoint).Path }
if (-not $Output) {
    $pending = Join-Path $projectRoot 'artifacts\live-acceptance\v2\authorizations\pending'
    New-Item -ItemType Directory -Force -Path $pending | Out-Null
    $Output = Join-Path $pending ("authorization-{0}-{1}.json" -f $Phase, [Guid]::NewGuid().ToString('N'))
}
$Output = [System.IO.Path]::GetFullPath($Output)

Write-Host 'Paid live-acceptance authorization contract:'
Write-Host "  phase: $Phase"
Write-Host "  release receipt: $receiptPath"
Write-Host "  checkpoint: $(if ($Checkpoint) { $Checkpoint } else { '<none>' })"
Write-Host "  profile: codex / $Model / $ReasoningEffort / workspace-write"
Write-Host "  timeout: $TimeoutSeconds seconds"
Write-Host "  expiry: $ExpiresMinutes minutes"
Write-Host '  worker network: model transport only; registry restore belongs to the supervisor'
$required = "AUTHORIZE $Phase"
$confirmation = Read-Host "Type '$required' to issue the one-use authorization"
if ($confirmation -cne $required) { throw 'LIVE_AUTHORIZATION_NOT_CONFIRMED: no authorization was written.' }

$arguments = @(
    (Join-Path $projectRoot 'tests\live\v2\cli.py'), 'authorize', '--phase', $Phase,
    '--release-receipt', $receiptPath, '--model', $Model, '--reasoning-effort', $ReasoningEffort,
    '--timeout-seconds', $TimeoutSeconds.ToString(), '--expires-minutes', $ExpiresMinutes.ToString(),
    '--output', $Output, '--confirmed'
)
if ($Checkpoint) { $arguments += @('--checkpoint', $Checkpoint) }
if ($Scenario) { $arguments += @('--scenario', ([System.IO.Path]::GetFullPath($Scenario))) }
& python @arguments
if ($LASTEXITCODE -ne 0) { throw "Live authorization issuance failed with exit code $LASTEXITCODE." }
