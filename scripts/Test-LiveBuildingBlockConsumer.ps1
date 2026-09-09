[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Authorization,
    [Parameter(Mandatory)]
    [string]$Checkpoint,
    [string]$Scenario = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$arguments = @(
    (Join-Path $projectRoot 'tests\live\v2\cli.py'), 'building-block-consumer',
    '--authorization', (Resolve-Path -LiteralPath $Authorization).Path,
    '--checkpoint', (Resolve-Path -LiteralPath $Checkpoint).Path
)
if ($Scenario) { $arguments += @('--scenario', ([System.IO.Path]::GetFullPath($Scenario))) }
& python @arguments
if ($LASTEXITCODE -ne 0) { throw "Live building-block consumer phase failed with exit code $LASTEXITCODE." }
