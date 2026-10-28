[CmdletBinding()]
param(
    [string]$Python = 'python',
    [string]$AssetsDir = 'artifacts'
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Push-Location $sourceRoot
try {
    # Reuse the actual release archive/native installation contract. No linked
    # source installation, workflow execution or coding agent is involved.
    & $Python (Join-Path $sourceRoot 'tests/validate_intake_install.py') --assets-dir $AssetsDir
    if ($LASTEXITCODE -ne 0) { throw 'Archive-native local installation failed; preserve its evidence.' }
}
finally {
    Pop-Location
}
