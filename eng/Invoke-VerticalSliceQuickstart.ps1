[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot
try {
    & (Join-Path $PSScriptRoot 'Bootstrap-DependencyMirror.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency mirror bootstrap failed.' }
    dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.Config
    if ($LASTEXITCODE -ne 0) { throw 'Locked restore failed.' }
    dotnet build ProgramKit.slnx --configuration Release --no-restore
    if ($LASTEXITCODE -ne 0) { throw 'Release build failed.' }
    dotnet test ProgramKit.slnx --configuration Release --no-build --no-restore
    if ($LASTEXITCODE -ne 0) { throw 'Vertical-slice tests failed.' }
    dotnet format ProgramKit.slnx --no-restore --verify-no-changes
    if ($LASTEXITCODE -ne 0) { throw 'Formatting verification failed.' }
}
finally {
    Pop-Location
}
