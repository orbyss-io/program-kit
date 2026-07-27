[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $PackageManifest,

    [Parameter(Mandatory = $true)]
    [string] $PublishRoot,

    [Parameter(Mandatory = $true)]
    [string] $ConsumerProof,

    [Parameter(Mandatory = $true)]
    [string] $OutputRoot
)

$ErrorActionPreference = 'Stop'

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    return "sha256:$((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant())"
}

$packageManifestPath = [IO.Path]::GetFullPath($PackageManifest)
$publishRootPath = [IO.Path]::GetFullPath($PublishRoot)
$consumerProofPath = [IO.Path]::GetFullPath($ConsumerProof)
$outputRootPath = [IO.Path]::GetFullPath($OutputRoot)
if (Test-Path -LiteralPath $outputRootPath) {
    throw "The W065 evidence output already exists: $outputRootPath"
}

$packageDocument = Get-Content -LiteralPath $packageManifestPath -Raw |
    ConvertFrom-Json -Depth 100
$consumerDocument = Get-Content -LiteralPath $consumerProofPath -Raw |
    ConvertFrom-Json -Depth 100
$packageDigest = Get-Sha256 -Path $packageManifestPath
if ($consumerDocument.packageRootManifestDigest -ne $packageDigest -or
    @($consumerDocument.consumers).Count -ne 5) {
    throw 'The isolated-consumer proof is not bound to the selected package root and five consumers.'
}

$publishEvidence = @()
$publishManifests = @(
    Get-ChildItem `
        -LiteralPath $publishRootPath `
        -Filter 'local-publish-manifest.json' `
        -File `
        -Recurse |
        Sort-Object FullName)
if ($publishManifests.Count -ne 3) {
    throw 'Exactly three local publish manifests are required.'
}

foreach ($manifest in $publishManifests) {
    $document = Get-Content -LiteralPath $manifest.FullName -Raw |
        ConvertFrom-Json -Depth 100
    if ($document.packageRootManifestDigest -ne $packageDigest) {
        throw "Publish manifest is bound to a different package root: $($manifest.FullName)"
    }

    $publishEvidence += [ordered]@{
        hostIdentity = $document.hostIdentity
        hostVersion = $document.hostVersion
        targetFramework = $document.targetFramework
        configuration = $document.configuration
        deploymentMode = $document.deploymentMode
        fileCount = @($document.files).Count
        manifestDigest = Get-Sha256 -Path $manifest.FullName
    }
}

$summary = [ordered]@{
    '$schema' = 'pkid:schema:program-kit:w065-local-package-publish-proof@1.0.0'
    version = '1.0.0'
    packageRoot = [ordered]@{
        manifestDigest = $packageDigest
        packageCount = @($packageDocument.packages).Count
        externalPackageCount = @($packageDocument.externalPackages).Count
        inputVersionMapRevision =
            $packageDocument.inputVersionMap.revision
        inputVersionSelectionRevision =
            $packageDocument.inputVersionSelection.revision
    }
    publishes = $publishEvidence
    isolatedConsumerProof = [ordered]@{
        digest = Get-Sha256 -Path $consumerProofPath
        consumerCount = @($consumerDocument.consumers).Count
        identities = @($consumerDocument.consumers.identity)
    }
    migrationClosure = [ordered]@{
        versionMapIdentity =
            'pkid:version-map:fixture:observatory-package-publish-extension'
        version = '3.0.0'
        impactCount = 28
        packageCount = 6
        isolatedConsumerCount = 5
        publishProfileCount = 3
        publishLeafCount = 3
        localPublishManifestCount = 3
    }
}

New-Item -ItemType Directory -Path $outputRootPath | Out-Null
$summaryPath = Join-Path $outputRootPath 'local-package-publish-proof.json'
[IO.File]::WriteAllText(
    $summaryPath,
    ($summary | ConvertTo-Json -Depth 10 -Compress),
    [Text.UTF8Encoding]::new($false))
Copy-Item `
    -LiteralPath $consumerProofPath `
    -Destination (Join-Path $outputRootPath 'isolated-consumer-proof.json')
Write-Output $summaryPath
