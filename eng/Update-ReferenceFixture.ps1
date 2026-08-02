[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
& dotnet run --file (Join-Path $PSScriptRoot 'UpdateReferenceFixture.cs')
if ($LASTEXITCODE -ne 0) {
    throw "Reference fixture generation failed with exit code $LASTEXITCODE."
}

git -C $repositoryRoot diff --check -- tests/Fixtures/Reference.Status/Valid
if ($LASTEXITCODE -ne 0) {
    throw 'Generated reference fixture contains invalid whitespace.'
}
