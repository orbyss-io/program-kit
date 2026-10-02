[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
# This is deliberately a human-owned launch. It creates a fresh Git repository,
# initializes Spec Kit and exercises native sandbox commands without a model.
if ($env:CODEX_SESSION_ID -or $env:CODEX_THREAD_ID -or $env:CODEX_INTERNAL_ORIGINATOR_OVERRIDE) {
    throw 'Open a normal user-owned PowerShell terminal to run this probe; do not launch it from a Codex agent.'
}
$probeScript = Join-Path $PSScriptRoot 'probe_codex_worker_permissions.py'
& python $probeScript
if ($LASTEXITCODE -ne 0) { throw 'Codex worker permission probe failed; inspect its preserved evidence.' }
