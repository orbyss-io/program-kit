[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string] $CanonicalBuildRoot,
    [Parameter(Mandatory = $true)][string] $Repository,
    [Parameter(Mandatory = $true)][string] $SourceCommit,
    [Parameter(Mandatory = $true)][string] $ProductVersion,
    [switch] $PlanOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($CanonicalBuildRoot)
$manifestPath = Join-Path $root 'package-manifest.json'
$checksumPath = Join-Path $root 'SHA256SUMS'
$provenancePath = Join-Path $root 'canonical-build-provenance.json'
if ($Repository -cnotmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' -or
    $SourceCommit -cnotmatch '^[0-9a-f]{40}$' -or
    $ProductVersion -cnotmatch '^[0-9]+\.[0-9]+\.[0-9]+-[0-9A-Za-z.-]+$') {
    throw 'The publication repository, source commit, or prerelease version is invalid.'
}

foreach ($evidencePath in @(
        $manifestPath,
        $checksumPath,
        $provenancePath)) {
    if (-not (Test-Path -LiteralPath $evidencePath -PathType Leaf)) {
        throw "Verified canonical-build evidence is absent: $evidencePath"
    }
}

$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$provenance = Get-Content -Raw -LiteralPath $provenancePath | ConvertFrom-Json
if ($manifest.productVersion -cne $ProductVersion -or
    $provenance.productVersion -cne $ProductVersion -or
    $provenance.sourceCommit -cne $SourceCommit) {
    throw 'The verified canonical build differs from the publication selection.'
}

$packages = @($manifest.packages)
if ($packages.Count -eq 0) {
    throw 'The verified canonical build contains no packages.'
}

$packagePaths = @()
$packageIds = @()
foreach ($package in $packages) {
    $packageId = [string] $package.packageId
    $filename = [string] $package.filename
    if ([string]::IsNullOrWhiteSpace($packageId) -or
        [IO.Path]::GetFileName($filename) -cne $filename -or
        $packageIds -ccontains $packageId) {
        throw 'The publication package selection is invalid or duplicated.'
    }

    $packagePath = Join-Path (Join-Path $root 'feed') $filename
    if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) {
        throw "A verified package is absent: $filename"
    }

    $packageIds += $packageId
    $packagePaths += $packagePath
}

$tag = "v$ProductVersion"
$releaseAssets = @(
    $packagePaths
    $manifestPath
    $checksumPath
    $provenancePath)
$plan = [ordered]@{
    planVersion = '0.1.0-alpha.1'
    repository = $Repository
    sourceCommit = $SourceCommit
    productVersion = $ProductVersion
    tag = $tag
    packages = @(
        for ($index = 0; $index -lt $packageIds.Count; $index++) {
            [ordered]@{
                packageId = $packageIds[$index]
                path = $packagePaths[$index]
            }
        })
    releaseAssets = @($releaseAssets)
}
if ($PlanOnly) {
    $plan | ConvertTo-Json -Depth 8
    return
}

$apiKey = [Environment]::GetEnvironmentVariable('NUGET_API_KEY')
$githubToken = [Environment]::GetEnvironmentVariable('GH_TOKEN')
if ([string]::IsNullOrWhiteSpace($apiKey) -or
    [string]::IsNullOrWhiteSpace($githubToken)) {
    throw 'Temporary NuGet and GitHub publication credentials are required.'
}

$matchingRefsJson = & gh api `
    "repos/$Repository/git/matching-refs/tags/$tag"
if ($LASTEXITCODE -ne 0) {
    throw "GitHub tag collision verification failed for $tag."
}

$matchingRefs = @($matchingRefsJson | ConvertFrom-Json)
if (@(
        $matchingRefs |
            Where-Object { $_.ref -ceq "refs/tags/$tag" }).Count -ne 0) {
    throw "The release tag already exists and cannot be hidden: $tag"
}

$releasePagesJson = & gh api `
    --paginate `
    --slurp `
    "repos/$Repository/releases?per_page=100"
if ($LASTEXITCODE -ne 0) {
    throw "GitHub release collision verification failed for $tag."
}

$releasePages = @($releasePagesJson | ConvertFrom-Json)
$releases = @($releasePages | ForEach-Object { $_ })
if (@(
        $releases |
            Where-Object { $_.tag_name -ceq $tag }).Count -ne 0) {
    throw "The GitHub release already exists and cannot be hidden: $tag"
}

$acceptedPackageIds = [Collections.Generic.List[string]]::new()
foreach ($package in $plan.packages) {
    & dotnet nuget push `
        $package.path `
        --source 'https://api.nuget.org/v3/index.json' `
        --api-key $apiKey
    if ($LASTEXITCODE -ne 0) {
        $accepted = if ($acceptedPackageIds.Count -eq 0) {
            '<none>'
        }
        else {
            $acceptedPackageIds -join ', '
        }
        throw "NuGet publication stopped at $(
            $package.packageId). Packages accepted before failure: $accepted"
    }

    $acceptedPackageIds.Add([string] $package.packageId)
}

$releaseArguments = @(
    'release',
    'create',
    $tag,
    '--repo',
    $Repository,
    '--target',
    $SourceCommit,
    '--title',
    $tag,
    '--generate-notes',
    '--prerelease')
$releaseArguments += $releaseAssets
& gh @releaseArguments
if ($LASTEXITCODE -ne 0) {
    throw "All packages were accepted, but durable release creation failed for $(
        $tag). Accepted packages: $($acceptedPackageIds -join ', ')"
}

Write-Output (
    "Published $($acceptedPackageIds.Count) exact packages and created $(
        $tag) at $SourceCommit.")
