[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $OutputRoot
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$resolvedOutput = if ([IO.Path]::IsPathRooted($OutputRoot)) {
    [IO.Path]::GetFullPath($OutputRoot)
}
else {
    [IO.Path]::GetFullPath((Join-Path $repositoryRoot $OutputRoot))
}

New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null

Push-Location $repositoryRoot
try {
    dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.Config
    if ($LASTEXITCODE -ne 0) { throw 'Locked restore failed.' }

    dotnet pack src/ProgramKit.Cli/ProgramKit.Cli.csproj `
        --configuration Release `
        --no-restore `
        --output $resolvedOutput `
        -p:ContinuousIntegrationBuild=true `
        -p:IncludeSymbols=true `
        -p:SymbolPackageFormat=snupkg
    if ($LASTEXITCODE -ne 0) { throw 'Program Kit tool packaging failed.' }
}
finally {
    Pop-Location
}
