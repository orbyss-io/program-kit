[CmdletBinding()]
param(
    [switch]$SkipTests,
    [Alias('SkipBundle')]
    [switch]$SkipRunnableHost,
    [switch]$LockedMode
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
New-Item -ItemType Directory -Force -Path $packages | Out-Null

if ($LockedMode) {
    dotnet restore $solutions[0].FullName --locked-mode
}
else {
    dotnet restore $solutions[0].FullName
}
if ($LASTEXITCODE -ne 0) { throw 'dotnet restore failed.' }
dotnet build $solutions[0].FullName -c Release --no-restore -p:Version=$version
if ($LASTEXITCODE -ne 0) { throw 'dotnet build failed.' }

if (-not $SkipTests) {
    dotnet test $solutions[0].FullName -c Release --no-build -p:Version=$version
    if ($LASTEXITCODE -ne 0) { throw 'dotnet test failed.' }
}

dotnet pack $solutions[0].FullName -c Release --no-build -p:Version=$version -p:PackageOutputPath=$packages
if ($LASTEXITCODE -ne 0) { throw 'dotnet pack failed.' }

if (-not $SkipRunnableHost) {
    python (Join-Path $PSScriptRoot 'runnable_host.py') stage --repository $root --packages $packages `
        --output (Join-Path $artifacts 'runnable-host')
    if ($LASTEXITCODE -ne 0) { throw 'Runnable-host staging failed.' }
}
