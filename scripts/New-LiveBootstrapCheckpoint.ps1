[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Authorization,
    [string]$Scenario = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$arguments = @((Join-Path $projectRoot 'tests\live\v2\cli.py'), 'bootstrap', '--authorization', (Resolve-Path -LiteralPath $Authorization).Path)
if ($Scenario) { $arguments += @('--scenario', ([System.IO.Path]::GetFullPath($Scenario))) }
& python @arguments
if ($LASTEXITCODE -ne 0) { throw "Live bootstrap checkpoint phase failed with exit code $LASTEXITCODE." }
