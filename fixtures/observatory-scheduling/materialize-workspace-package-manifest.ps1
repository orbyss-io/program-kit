[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$PackageRoot
)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$manifestPath = Join-Path $PSScriptRoot 'workspace-package-manifest.json'
$resolvedPackageRoot = [IO.Path]::GetFullPath($PackageRoot)
if (-not (Test-Path -LiteralPath $resolvedPackageRoot -PathType Container)) {
    throw "Package root does not exist: $resolvedPackageRoot"
}

[xml]$buildProperties = Get-Content -Raw -LiteralPath (
    Join-Path $repoRoot 'Directory.Build.props')
$productVersion = [string](
    $buildProperties.Project.PropertyGroup.Version |
        Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } |
        Select-Object -First 1)
$productVersion = $productVersion.Trim()
if ($productVersion -ne '0.1.0-alpha.2') {
    throw "Expected the coordinated Program Kit product version 0.1.0-alpha.2; observed $productVersion."
}

$existing = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
$fixturePackages = @(
    $existing.packages |
        Where-Object packageRole -eq 'fixture' |
        Sort-Object packageId)
$programKitPackages = @(
    Get-ChildItem -LiteralPath (Join-Path $repoRoot 'src') `
            -Recurse `
            -Filter '*.csproj' |
        Sort-Object BaseName |
        ForEach-Object {
            $packageId = $_.BaseName
            $fileName = "$packageId.$productVersion.nupkg"
            $packagePath = Join-Path $resolvedPackageRoot $fileName
            if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) {
                throw "The exact coordinated package is missing: $packagePath"
            }

            $identityName = $packageId.Replace('.', '-').ToLowerInvariant()
            $packageIdentity = "pkid:package:program-kit:$identityName"
            $revisionDigest = 'sha256:' + [Convert]::ToHexString(
                    [Security.Cryptography.SHA256]::HashData(
                        [Text.Encoding]::UTF8.GetBytes(
                            "$packageIdentity@$productVersion"))).
                ToLowerInvariant()
            $sourcePath = [IO.Path]::GetRelativePath(
                    $repoRoot,
                    $_.FullName).
                Replace('\', '/')
            [ordered]@{
                expectedTarget = 'net10.0'
                packageId = $packageId
                packageOutputPath = $fileName
                packageRevision = [ordered]@{
                    digest = $revisionDigest
                    identity = $packageIdentity
                    version = $productVersion
                }
                packageRole = 'program-kit'
                sourceProjectIdentity =
                    "pkid:project:program-kit:$identityName"
                sourceProjectPath = $sourcePath
            }
        })

if ($programKitPackages.Count -ne 29) {
    throw "Expected exactly 29 first-party Program Kit packages; observed $($programKitPackages.Count)."
}

$manifest = [ordered]@{
    '$schema' = $existing.'$schema'
    externalPackages = $existing.externalPackages
    inputVersionMap = $existing.inputVersionMap
    inputVersionSelection = $existing.inputVersionSelection
    packProjectPath = $existing.packProjectPath
    packages = @($fixturePackages) + @($programKitPackages)
    sourceRoot = $existing.sourceRoot
    version = $existing.version
}

$json = ($manifest | ConvertTo-Json -Depth 100 -Compress) + "`n"
[IO.File]::WriteAllText(
    $manifestPath,
    $json,
    [Text.UTF8Encoding]::new($false))
Write-Output (
    "Materialized {0} fixture and {1} Program Kit package selections at {2}." -f
        $fixturePackages.Count,
        $programKitPackages.Count,
        $productVersion)
