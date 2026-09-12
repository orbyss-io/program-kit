[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('bootstrap-checkpoint', 'building-block-consumer', 'feature-intake', 'feature-planning', 'feature-plan-tasks', 'feature-setup', 'feature-delivery', 'upgrade-consumer')]
    [string]$Phase,
    [string]$ReleaseReceipt = '',
    [string]$TrialReceipt = '',
    [string]$Checkpoint = '',
    [ValidateSet('', 'fresh-baseline', 'fresh-candidate', 'upgrade-candidate')]
    [string]$Case = '',
    [string]$ReleaseRoot = '',
    [string]$BaselineReport = '',
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
if ([bool]$ReleaseReceipt -eq [bool]$TrialReceipt) { throw 'Select exactly one -ReleaseReceipt or -TrialReceipt.' }
$receiptKind = if ($TrialReceipt) { 'development-trial' } else { 'release' }
$receiptPath = (Resolve-Path -LiteralPath $(if ($TrialReceipt) { $TrialReceipt } else { $ReleaseReceipt })).Path
$receiptDetails = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
if ($Phase -notin @('bootstrap-checkpoint', 'building-block-consumer') -and -not $Case) { throw 'LIVE_SYNC_CASE_REQUIRED: select the exact baseline, candidate or upgrade case.' }
if ($Phase -eq 'upgrade-consumer' -and -not $BaselineReport) { throw 'LIVE_SYNC_UPGRADE_BASELINE_ACCEPTANCE_REQUIRED: first complete independent functional acceptance of the baseline case.' }
if ($Phase -ne 'bootstrap-checkpoint' -and -not $Checkpoint) {
    throw 'LIVE_AUTHORIZATION_CHECKPOINT_REQUIRED: building-block-consumer authorization must bind a checkpoint.'
}
if ($Checkpoint) { $Checkpoint = (Resolve-Path -LiteralPath $Checkpoint).Path }
if (-not $Output) {
    $pending = Join-Path $projectRoot 'artifacts\live-acceptance\v2\authorizations\pending'
    New-Item -ItemType Directory -Force -Path $pending | Out-Null
    $Output = Join-Path $pending ("authorization-{0}-{1}.json" -f $Phase, [Guid]::NewGuid().ToString('N'))
}
$Output = [System.IO.Path]::GetFullPath($Output)
$codexCommand = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codexCommand) { throw 'LIVE_ACCEPTANCE_TOOL_MISSING: codex' }
$codexVersionOutput = @(& $codexCommand.Source --version 2>&1)
$codexExitCode = $LASTEXITCODE
$launcherVersion = [string]($codexVersionOutput | ForEach-Object { [string]$_ } | Where-Object { $_ -match '^codex-cli\s+\S+' } | Select-Object -First 1)
if ($codexExitCode -ne 0 -or -not $launcherVersion) {
    throw 'LIVE_ACCEPTANCE_TOOL_UNUSABLE: codex --version failed.'
}

$previewArguments = @((Join-Path $projectRoot 'tests/live/v2/cli.py'), 'session-limit',
    '--phase', $Phase, '--release-receipt', $receiptPath, '--receipt-kind', $receiptKind)
if ($ReleaseRoot) { $previewArguments += @('--release-root', (Resolve-Path -LiteralPath $ReleaseRoot).Path) }
$previewOutput = @(& python @previewArguments)
if ($LASTEXITCODE -ne 0 -or $previewOutput.Count -ne 1 -or $previewOutput[0] -notmatch '^\d+$') {
    throw 'Could not verify the paid-session limit from the candidate receipt and packaged workflow.'
}
$maximumPaidSessions = [int]$previewOutput[0]

Write-Host 'Paid live-acceptance authorization contract:'
Write-Host "  phase: $Phase"
Write-Host "  case: $Case"
Write-Host "  release source: $ReleaseRoot"
Write-Host "  baseline acceptance report: $BaselineReport"
Write-Host "  receipt kind: $receiptKind"
Write-Host "  candidate receipt: $receiptPath"
Write-Host "  candidate commit: $($receiptDetails.source.commit)"
Write-Host "  receipt status: $($receiptDetails.status)"
Write-Host "  checkpoint: $(if ($Checkpoint) { $Checkpoint } else { '<none>' })"
Write-Host "  profile: codex / $Model / $ReasoningEffort / workspace-write"
Write-Host "  Codex launcher: $launcherVersion"
Write-Host "  timeout: $TimeoutSeconds seconds"
Write-Host "  maximum paid sessions: $maximumPaidSessions (verified against the candidate package)"
Write-Host "  expiry: $ExpiresMinutes minutes"
Write-Host '  worker network: model transport only; registry restore belongs to the supervisor'
$required = "AUTHORIZE $Phase"
$confirmation = Read-Host "Type '$required' to issue the one-use authorization"
if ($confirmation -cne $required) { throw 'LIVE_AUTHORIZATION_NOT_CONFIRMED: no authorization was written.' }

$arguments = @(
    (Join-Path $projectRoot 'tests\live\v2\cli.py'), 'authorize', '--phase', $Phase,
    '--release-receipt', $receiptPath, '--receipt-kind', $receiptKind, '--model', $Model, '--reasoning-effort', $ReasoningEffort,
    '--displayed-session-limit', $maximumPaidSessions.ToString(),
    '--launcher-version', $launcherVersion,
    '--timeout-seconds', $TimeoutSeconds.ToString(), '--expires-minutes', $ExpiresMinutes.ToString(),
    '--output', $Output, '--confirmed'
)
if ($Checkpoint) { $arguments += @('--checkpoint', $Checkpoint) }
if ($Case) { $arguments += @('--case', $Case) }
if ($ReleaseRoot) { $arguments += @('--release-root', (Resolve-Path -LiteralPath $ReleaseRoot).Path) }
if ($BaselineReport) { $arguments += @('--baseline-report', (Resolve-Path -LiteralPath $BaselineReport).Path) }
if ($Scenario) { $arguments += @('--scenario', ([System.IO.Path]::GetFullPath($Scenario))) }
& python @arguments
if ($LASTEXITCODE -ne 0) { throw "Live authorization issuance failed with exit code $LASTEXITCODE." }
