[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $AdapterRoot
)

$ErrorActionPreference = 'Stop'
$entrypoint = Join-Path ([IO.Path]::GetFullPath($AdapterRoot)) 'tools/program-kit-spec-kit-adapter.dll'
if (-not (Test-Path -LiteralPath $entrypoint -PathType Leaf)) {
    throw "Adapter entrypoint is missing: $entrypoint"
}

$version = & dotnet $entrypoint --version
if ($LASTEXITCODE -ne 0) { throw 'Adapter version smoke failed.' }
$result = $version | ConvertFrom-Json
if ($result.adapter -ne 'orbyss-program-kit-adapter' -or $result.version -ne '0.1.0') {
    throw 'Adapter version identity is not exact.'
}
$version
