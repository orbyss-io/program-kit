[CmdletBinding()]
param(
    [switch]$IdentityOnly,
    [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$compose = Join-Path $repository 'deploy\compose.identity.yml'
$applicationCompose = Join-Path $repository 'deploy\compose.application.yml'

python (Join-Path $PSScriptRoot 'preflight.py')
if ($LASTEXITCODE -ne 0) { throw 'Program Kit pre-host prerequisites failed.' }

docker compose -f $compose up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'The pinned local Keycloak service did not become ready.' }

if ($IdentityOnly) {
    Write-Host 'Local identity is ready at http://localhost:8080 (realm program-kit).'
    exit 0
}

if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot 'Build.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'The application build failed.' }
}

if ([string]::IsNullOrWhiteSpace($env:PROGRAMKIT_HOST_IMAGE)) {
    throw 'Set PROGRAMKIT_HOST_IMAGE to the approved digest-pinned ProgramKit.Host image, then rerun Dev.ps1. Identity remains ready.'
}

$applicationImage = 'program-kit-consumer:local'
docker build --build-arg "PROGRAMKIT_HOST_IMAGE=$($env:PROGRAMKIT_HOST_IMAGE)" -t $applicationImage $repository
if ($LASTEXITCODE -ne 0) { throw 'The local application image build failed.' }

docker compose -f $applicationCompose up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'The local application did not become ready.' }
