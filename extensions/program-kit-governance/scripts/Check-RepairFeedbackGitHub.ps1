[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'repair_feedback.py'
& python $scriptPath prerequisites
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Follow https://cli.github.com/ for Windows installer or winget, macOS or Linux guidance. Add the actual install directory to PATH, reopen your shell, then run gh auth login --hostname github.com yourself. No install or login was attempted.'
    exit 1
}
