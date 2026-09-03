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
$cache = Join-Path $root '.program-kit/cache'
$nugetConfig = Join-Path $root 'NuGet.config'
if (-not (Test-Path -LiteralPath $nugetConfig -PathType Leaf)) {
    throw "Managed restore requires the reviewed repository NuGet.config: $nugetConfig"
}
$env:NUGET_PACKAGES = Join-Path $cache 'nuget/packages'
$env:NUGET_HTTP_CACHE_PATH = Join-Path $cache 'nuget/http'
New-Item -ItemType Directory -Force -Path $env:NUGET_PACKAGES, $env:NUGET_HTTP_CACHE_PATH | Out-Null
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
    dotnet restore $solutions[0].FullName --locked-mode --configfile $nugetConfig
}
else {
    dotnet restore $solutions[0].FullName --configfile $nugetConfig
}
if ($LASTEXITCODE -ne 0) { throw 'dotnet restore failed.' }
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
    python (Join-Path $PSScriptRoot 'toolchain.py') --repository $root `
        --evidence (Join-Path $root '.program-kit/evidence/toolchain.json')
    if ($LASTEXITCODE -ne 0) {
        throw 'Pinned toolchain verification failed. Install or select the Program Kit Node pin; only an explicit managed-toolchain-version decision may retain another local version.'
    }
    $openApiArguments = @('--repository', $root, '--registry', '.program-kit/openapi-contracts.json')
    if ($InitializeOpenApiBaseline) { $openApiArguments += '--initialize-baselines' }
    if ($UpdateOpenApiArtifact) { $openApiArguments += '--update-artifacts' }
    python (Join-Path $PSScriptRoot 'openapi_pipeline.py') @openApiArguments
    if ($LASTEXITCODE -ne 0) { throw 'Producer-first OpenAPI contract pipeline failed.' }
}
