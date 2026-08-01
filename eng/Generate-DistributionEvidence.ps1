[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Push-Location $repositoryRoot
try {
    & dotnet run --file (Join-Path $PSScriptRoot 'GenerateDistributionEvidence.cs')
    if ($LASTEXITCODE -ne 0) {
        throw "Distribution evidence generation failed with exit code $LASTEXITCODE."
    }
    git diff --check -- artifacts/evidence
    if ($LASTEXITCODE -ne 0) {
        throw 'Generated distribution evidence contains invalid whitespace.'
    }
}
finally {
    Pop-Location
}
