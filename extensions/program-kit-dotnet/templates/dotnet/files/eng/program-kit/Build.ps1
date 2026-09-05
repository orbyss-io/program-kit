[CmdletBinding()]
param(
    [switch]$SkipTests,
    [Alias('SkipBundle')]
    [switch]$SkipRunnableHost,
    [switch]$LockedMode,
    [switch]$InitializeOpenApiBaseline,
    [switch]$UpdateOpenApiArtifact
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$version = (Get-Content -Raw -LiteralPath (Join-Path $root 'VERSION')).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+([-.][0-9A-Za-z.-]+)?$') {
    throw "VERSION is not a valid SemVer value: '$version'"
}

$solutions = @(Get-ChildItem -LiteralPath $root -File | Where-Object { $_.Extension -in '.sln', '.slnx' })
if ($solutions.Count -ne 1) {
    throw "Expected exactly one solution in $root; found $($solutions.Count)."
}

$artifacts = Join-Path $root 'artifacts'
$packages = Join-Path (Join-Path $artifacts 'packages') $version
$openApiRegistry = Join-Path $root '.program-kit/openapi-contracts.json'
$openApiEnabled = $false
if (Test-Path -LiteralPath $openApiRegistry) {
    $openApiConfiguration = Get-Content -Raw -LiteralPath $openApiRegistry | ConvertFrom-Json
    if ($openApiConfiguration.schemaVersion -ne 1 -or $null -eq $openApiConfiguration.contracts) {
        throw 'OpenAPI registry must use schemaVersion 1 and declare a contracts array.'
    }
    $openApiEnabled = @($openApiConfiguration.contracts).Count -gt 0
}
New-Item -ItemType Directory -Force -Path $packages | Out-Null

if ($LockedMode) {
    & (Join-Path $PSScriptRoot 'Restore.ps1') -Subject $solutions[0].FullName -LockedMode
}
else {
    & (Join-Path $PSScriptRoot 'Restore.ps1') -Subject $solutions[0].FullName
}
if (-not $?) { throw 'Managed repository-isolated restore failed.' }
dotnet build $solutions[0].FullName -c Release --no-restore -p:Version=$version
if ($LASTEXITCODE -ne 0) { throw 'dotnet build failed.' }

if (-not $SkipTests) {
    dotnet test --solution $solutions[0].FullName -c Release --no-build -p:Version=$version
    if ($LASTEXITCODE -ne 0) { throw 'dotnet test failed.' }
}

dotnet pack $solutions[0].FullName -c Release --no-build -p:Version=$version -p:PackageOutputPath=$packages
if ($LASTEXITCODE -ne 0) { throw 'dotnet pack failed.' }

if (-not $SkipRunnableHost -or $openApiEnabled) {
    python (Join-Path $PSScriptRoot 'runnable_host.py') stage --repository $root --packages $packages `
        --output (Join-Path $artifacts 'runnable-host')
    if ($LASTEXITCODE -ne 0) { throw 'Runnable-host staging failed.' }
}

if ($openApiEnabled) {
    $openApiArguments = @('--repository', $root, '--registry', '.program-kit/openapi-contracts.json')
    if ($InitializeOpenApiBaseline) { $openApiArguments += '--initialize-baselines' }
    if ($UpdateOpenApiArtifact) { $openApiArguments += '--update-artifacts' }
    python (Join-Path $PSScriptRoot 'openapi_pipeline.py') @openApiArguments
    if ($LASTEXITCODE -ne 0) { throw 'Producer-first OpenAPI contract pipeline failed.' }
}
