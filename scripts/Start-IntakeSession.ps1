[CmdletBinding()]
param(
    [string]$Model = '',
    [switch]$KeepWorkspace,
    [switch]$PrepareOnly
)

$ErrorActionPreference = 'Stop'
if (-not $PrepareOnly -and ($env:CODEX_THREAD_ID -or $env:CI -or
    $Host.Name -eq 'Windows PowerShell ISE Host' -or [Console]::IsInputRedirected)) {
    throw 'INTAKE_INTERACTIVE_TERMINAL_REQUIRED: run this yourself in a fresh PowerShell console.'
}
$sourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$record = Join-Path $sourceRoot ('artifacts\intake-sessions\' + [Guid]::NewGuid().ToString('N'))
$helper = Join-Path $PSScriptRoot 'intake_session.py'
$python = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$codex = if (-not $PrepareOnly) {
    # Prefer a native executable or cmd shim over an npm ps1 shim subject to execution policy.
    (Get-Command codex -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
}
$previousPreference = $ErrorActionPreference
$previousUtf8 = $env:PYTHONUTF8
$sessionExit = 1
try {
    $env:PYTHONUTF8 = '1'
    # Native stderr is not itself failure in Windows PowerShell 5.1. Exit codes are authoritative.
    $ErrorActionPreference = 'Continue'
    & $python $helper prepare --record $record
    if ($LASTEXITCODE -ne 0) { throw "Intake setup failed. Evidence: $record" }
    $state = Get-Content -Raw -LiteralPath (Join-Path $record 'session.json') | ConvertFrom-Json
    if ($PrepareOnly) { $sessionExit = 0 }
    else {
        Write-Host "Review evidence: $record"
        Write-Host 'This opens an interactive Codex intake using your normal login and configured model (unless -Model is given). Normal model usage applies.'
        Write-Host 'The conversation and workspace are saved locally for review. Do not enter secrets. Exit Codex with /quit when finished; bootstrap will not be started.'
        $idea = Read-Host 'What product do you want to build? (You can elaborate inside Codex)'
        if ([string]::IsNullOrWhiteSpace($idea)) { throw 'A product idea is required.' }
        [IO.File]::WriteAllText((Join-Path $state.workspace 'product-idea.md'), $idea, (New-Object Text.UTF8Encoding($false)))
        $arguments = @('--cd', $state.workspace, '--sandbox', 'workspace-write',
            '--ask-for-approval', 'on-request', '--no-alt-screen')
        if ($Model) { $arguments += @('--model', $Model) }
        $arguments += 'Read INTAKE-SESSION.md and follow the installed bootstrap intake skill using product-idea.md. Conduct the interview with me here. Stop at intake; do not launch bootstrap.'
        # Foreground with inherited console: never pipe the TUI or start a detached worker.
        & $codex @arguments
        $sessionExit = $LASTEXITCODE
    }
}
finally {
    try {
        if (Test-Path -LiteralPath (Join-Path $record 'session.json')) {
            $finishArguments = @($helper, 'finish', '--record', $record, '--exit-code', "$sessionExit")
            if ($KeepWorkspace) { $finishArguments += '--keep-workspace' }
            if ($PrepareOnly) { $finishArguments += '--prepare-only' }
            & $python @finishArguments
            if ($LASTEXITCODE -ne 0) { throw "Preservation or cleanup needs attention. See $record; keep its archive and session.json for recovery." }
        }
    }
    finally {
        $env:PYTHONUTF8 = $previousUtf8
        $ErrorActionPreference = $previousPreference
    }
}
if ($sessionExit -ne 0) { throw "Intake session ended with exit code $sessionExit. Review evidence: $record" }
