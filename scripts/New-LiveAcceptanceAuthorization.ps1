[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('bootstrap-checkpoint', 'building-block-consumer', 'workflow-fresh', 'workflow-failure', 'workflow-resume')]
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
    [string]$Fixture = 'price-calculator-approved-intake',
    [string]$FixtureVersion = '1',
    [string]$Verdict = '',
    [string]$Output = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$receiptPath = (Resolve-Path -LiteralPath $ReleaseReceipt).Path
if ($Phase -in @('building-block-consumer', 'workflow-resume') -and -not $Checkpoint) {
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

Write-Host 'Paid live-acceptance authorization contract:'
Write-Host "  phase: $Phase"
Write-Host "  release receipt: $receiptPath"
Write-Host "  checkpoint: $(if ($Checkpoint) { $Checkpoint } else { '<none>' })"
Write-Host "  profile: codex / $Model / $ReasoningEffort / workspace-write"
Write-Host "  Codex launcher: $launcherVersion"
Write-Host "  timeout: $TimeoutSeconds seconds"
Write-Host "  expiry: $ExpiresMinutes minutes"
Write-Host '  worker network: model transport only; registry restore belongs to the supervisor'
if ($Phase.StartsWith('workflow-')) {
    Write-Host "  fixture: $Fixture @ $FixtureVersion"
    Write-Host '  at most 8 paid command dispatches, stopping at the next human gate or terminal outcome'
    Write-Host "  reviewed gate verdict: $(if ($Verdict) { $Verdict } else { '<none>' })"
    Write-Host '  each subsequent paid continuation requires its own one-use authorization bound to the saved checkpoint'
    if ($Phase -eq 'workflow-failure') { Write-Host '  controlled fault: replace an actually READY report immediately before the native readiness requirement' }
    if ($Checkpoint) {
        & python (Join-Path $projectRoot 'tests\live\v2\workflow_acceptance.py') inspect-parent --checkpoint $Checkpoint
        if ($LASTEXITCODE -ne 0) { throw 'LIVE_WORKFLOW_PARENT_INVALID: no authorization was issued.' }
    }
}
$required = "AUTHORIZE $Phase"
$confirmation = Read-Host "Type '$required' to issue the one-use authorization"
if ($confirmation -cne $required) { throw 'LIVE_AUTHORIZATION_NOT_CONFIRMED: no authorization was written.' }

$arguments = @(
    (Join-Path $projectRoot 'tests\live\v2\cli.py'), 'authorize', '--phase', $Phase,
    '--release-receipt', $receiptPath, '--model', $Model, '--reasoning-effort', $ReasoningEffort,
    '--launcher-version', $launcherVersion,
    '--timeout-seconds', $TimeoutSeconds.ToString(), '--expires-minutes', $ExpiresMinutes.ToString(),
    '--output', $Output, '--confirmed'
)
if ($Checkpoint) { $arguments += @('--checkpoint', $Checkpoint) }
if ($Scenario -and -not $Phase.StartsWith('workflow-')) { $arguments += @('--scenario', ([System.IO.Path]::GetFullPath($Scenario))) }
if ($Phase.StartsWith('workflow-')) {
    $arguments[0] = Join-Path $projectRoot 'tests\live\v2\workflow_acceptance.py'
    $arguments += @('--fixture', $Fixture, '--fixture-version', $FixtureVersion)
    if ($Verdict) { $arguments += @('--verdict', $Verdict) }
}
& python @arguments
if ($LASTEXITCODE -ne 0) { throw "Live authorization issuance failed with exit code $LASTEXITCODE." }
