[CmdletBinding()]
param(
    [ValidateSet('codex', 'claude')]
    [string]$Integration = 'codex',

    [ValidateSet('clean-bootstrap')]
    [string]$Scenario = 'clean-bootstrap',

    [ValidateRange(60, 86400)]
    [int]$TimeoutSeconds = 7200,

    [switch]$Approved
)

$ErrorActionPreference = 'Stop'

if (-not $Approved) {
    throw @'
LIVE_ACCEPTANCE_APPROVAL_REQUIRED

This suite starts paid coding-agent sessions and can run for a long time.
Before publishing, ask the user whether to run the live bootstrap acceptance suite.
Run this script with -Approved only after the user explicitly answers yes.
'@
}

if ($env:CI -or $env:GITHUB_ACTIONS -or $env:TF_BUILD -or $env:BUILD_BUILDID) {
    throw 'LIVE_ACCEPTANCE_CI_FORBIDDEN: The paid live bootstrap suite must not run in CI.'
}

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$uv = Get-Command uv -ErrorAction Stop
$toolRoot = (& $uv.Source tool dir).Trim()

if ($IsWindows -or $env:OS -eq 'Windows_NT') {
    $python = Join-Path $toolRoot 'specify-cli\Scripts\python.exe'
} else {
    $python = Join-Path $toolRoot 'specify-cli/bin/python'
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Could not locate the specify-cli Python environment at $python"
}

$runner = Join-Path $projectRoot 'tests\live\run_bootstrap_acceptance.py'
& $python $runner `
    --scenario $Scenario `
    --integration $Integration `
    --timeout-seconds $TimeoutSeconds `
    --approved
if ($LASTEXITCODE -ne 0) {
    throw "Live bootstrap acceptance failed with exit code $LASTEXITCODE. Inspect artifacts/live-acceptance."
}

Write-Host 'Live bootstrap acceptance passed.'
