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
$stageRoot = Join-Path $resolvedOutput 'orbyss-program-kit-adapter-0.1.0'
$publishRoot = Join-Path $stageRoot 'tools'
$archivePath = Join-Path $resolvedOutput 'orbyss-program-kit-adapter-0.1.0.zip'

if (Test-Path -LiteralPath $stageRoot) { Remove-Item -LiteralPath $stageRoot -Recurse -Force }
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repositoryRoot 'extensions/orbyss-program-kit-adapter') -Destination $stageRoot -Recurse

dotnet publish (Join-Path $repositoryRoot 'src/ProgramKit.SpecKitAdapter/ProgramKit.SpecKitAdapter.csproj') `
    --configuration Release `
    --no-restore `
    --output $publishRoot `
    -p:ContinuousIntegrationBuild=true
if ($LASTEXITCODE -ne 0) { throw 'Spec Kit adapter publish failed.' }

if (Test-Path -LiteralPath $archivePath) { Remove-Item -LiteralPath $archivePath -Force }
Compress-Archive -Path (Join-Path $stageRoot '*') -DestinationPath $archivePath
[pscustomobject]@{ StageRoot = $stageRoot; ArchivePath = $archivePath } | ConvertTo-Json -Compress
