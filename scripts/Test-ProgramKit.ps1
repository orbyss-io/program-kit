[CmdletBinding()]
param(
    [ValidateSet('Integrity', 'Development', 'Affected', 'Baseline')]
    [string]$Suite = 'Integrity',
    [string]$ChangedFrom = '',
    [string[]]$Checks = @(),
    [string]$Reason = '',
    [string]$Python = 'python',
    [string]$BrowserEngines = $(if ($env:OS -eq 'Windows_NT') { 'chromium,webkit' } else { 'chromium,firefox,webkit' }),
    [switch]$List
)
$ErrorActionPreference = 'Stop'
# Every selected check owns its prerequisites; listing requires only Python.
$arguments = @((Join-Path $PSScriptRoot 'run_validation.py'), '--suite', $Suite, "--engines=$BrowserEngines")
if ($ChangedFrom) { $arguments += @('--changed-from', $ChangedFrom) }
foreach ($check in $Checks) { $arguments += @('--check', $check) }
if ($Reason) { $arguments += @('--reason', $Reason) }
if ($List) { $arguments += '--list' }
$previousUtf8 = $env:PYTHONUTF8
try {
    $env:PYTHONUTF8 = '1'
    & $Python @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Validation has failures, coverage gaps, missing prerequisites or budget overruns. Inspect the printed local results.' }
} finally {
    if ($null -eq $previousUtf8) { Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue }
    else { $env:PYTHONUTF8 = $previousUtf8 }
}
