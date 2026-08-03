[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('Debug', 'ContractLoop', 'PrePr', 'Release')]
    [string]$Configuration = 'Release',

    [Parameter()]
    [switch]$NoBuild
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$arguments = @(
    'test',
    'tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj',
    '--configuration', $Configuration,
    '--no-restore',
    '--filter', 'FullyQualifiedName~SpecKitAdapterQuickstartAcceptanceTests'
)
if ($NoBuild) { $arguments += '--no-build' }

Push-Location $repositoryRoot
try {
    & dotnet @arguments
    if ($LASTEXITCODE -ne 0) {
        throw 'The two clean packaged Spec Kit adapter journeys failed.'
    }
}
finally {
    Pop-Location
}
