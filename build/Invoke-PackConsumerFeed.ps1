[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $OutputRoot,

    [switch] $PlanOnly
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot '..'))
$outputPath = [IO.Path]::GetFullPath($OutputRoot)
$manifestPath = Join-Path $PSScriptRoot 'program-kit-release-packages.json'
$versionSourcePath = Join-Path $repositoryRoot 'Directory.Build.props'
$solutionPath = Join-Path $repositoryRoot 'ProgramKit.sln'
$packProjectPath = Join-Path $PSScriptRoot 'ProgramKit.Pack.proj'
$allowedRoles = @(
    'analyzer',
    'build-integration',
    'capability-bundle',
    'library',
    'tool')

function Assert-ExactProperties {
    param(
        [Parameter(Mandatory = $true)][psobject] $Value,
        [Parameter(Mandatory = $true)][string[]] $Expected,
        [Parameter(Mandatory = $true)][string] $Path
    )

    $actual = @($Value.PSObject.Properties.Name | Sort-Object)
    $expectedSorted = @($Expected | Sort-Object)
    if (($actual -join "`n") -cne ($expectedSorted -join "`n")) {
        throw "The release-package manifest has unexpected properties at ${Path}: $($actual -join ', ')."
    }
}

function Get-ProjectPackageId {
    param([Parameter(Mandatory = $true)][string] $ProjectPath)

    [xml] $project = Get-Content -LiteralPath $ProjectPath -Raw
    $packageId = @(
        $project.Project.PropertyGroup.PackageId |
            Where-Object { -not [string]::IsNullOrWhiteSpace([string] $_) } |
            Select-Object -First 1)
    if ($packageId.Count -eq 0) {
        return [IO.Path]::GetFileNameWithoutExtension($ProjectPath)
    }

    return [string] $packageId[0]
}

function Get-ProjectFirstPartyDependencies {
    param([Parameter(Mandatory = $true)][string] $ProjectPath)

    [xml] $project = Get-Content -LiteralPath $ProjectPath -Raw
    $dependencies = foreach ($reference in @(
            $project.Project.ItemGroup.ProjectReference)) {
        if ($null -eq $reference) {
            continue
        }

        $referencePath = [IO.Path]::GetFullPath(
            (Join-Path (
                Split-Path -Parent $ProjectPath) ([string] $reference.Include)))
        Get-ProjectPackageId -ProjectPath $referencePath
    }

    return @($dependencies | Sort-Object -Unique)
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    return "sha256:$((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant())"
}

function Invoke-CheckedDotNet {
    param(
        [Parameter(Mandatory = $true)][string[]] $Arguments,
        [Parameter(Mandatory = $true)][string] $Phase
    )

    & dotnet @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "The $Phase phase failed with exit code $LASTEXITCODE."
    }
}

function Write-PackageSelectionProps {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string[]] $Projects
    )

    $settings = [Xml.XmlWriterSettings]::new()
    $settings.Encoding = [Text.UTF8Encoding]::new($false)
    $settings.Indent = $true
    $settings.NewLineChars = "`n"
    $writer = [Xml.XmlWriter]::Create($Path, $settings)
    try {
        $writer.WriteStartElement('Project')
        $writer.WriteStartElement('ItemGroup')
        foreach ($project in $Projects) {
            $writer.WriteStartElement('_ProgramKitManifestPackageProject')
            $writer.WriteAttributeString('Include', $project)
            $writer.WriteEndElement()
        }

        $writer.WriteEndElement()
        $writer.WriteEndElement()
    }
    finally {
        $writer.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "The canonical release-package manifest is absent: $manifestPath"
}

if (Test-Path -LiteralPath $outputPath) {
    throw "The consumer-feed output must be a new path: $outputPath"
}

$manifestText = [IO.File]::ReadAllText($manifestPath)
$manifest = $manifestText | ConvertFrom-Json
Assert-ExactProperties `
    -Value $manifest `
    -Expected @('manifestVersion', 'packages', 'productVersion') `
    -Path '/'
if ($manifest.manifestVersion -cne '0.1.0-alpha.1') {
    throw 'The release-package manifest format is unsupported.'
}

if ($manifest.productVersion -cnotmatch '^0\.1\.0-alpha\.[1-9][0-9]*$') {
    throw 'The release-package manifest productVersion is not an exact Program Kit alpha version.'
}

[xml] $versionSource = Get-Content -LiteralPath $versionSourcePath -Raw
$sourceVersion = [string] (
    $versionSource.Project.PropertyGroup.Version |
        Where-Object { -not [string]::IsNullOrWhiteSpace([string] $_) } |
        Select-Object -First 1)
$sourcePackageVersion = [string] (
    $versionSource.Project.PropertyGroup.PackageVersion |
        Where-Object { -not [string]::IsNullOrWhiteSpace([string] $_) } |
        Select-Object -First 1)
if ($manifest.productVersion -cne $sourceVersion -or
    $manifest.productVersion -cne $sourcePackageVersion) {
    throw 'Directory.Build.props Version, PackageVersion, and the canonical release-package manifest must match exactly.'
}

$packages = @($manifest.packages)
if ($packages.Count -eq 0) {
    throw 'The release-package manifest must select at least one package.'
}

$packageIds = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
$projectPaths = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
foreach ($package in $packages) {
    Assert-ExactProperties `
        -Value $package `
        -Expected @(
            'packageId',
            'projectPath',
            'role',
            'coordinatedVersionRequired',
            'firstPartyDependencies') `
        -Path "/packages/$($package.packageId)"
    if ([string]::IsNullOrWhiteSpace($package.packageId) -or
        -not $package.packageId.StartsWith(
            'Orbyss.ProgramKit.',
            [StringComparison]::Ordinal)) {
        throw "Invalid first-party package ID: $($package.packageId)"
    }

    if (-not $packageIds.Add([string] $package.packageId)) {
        throw "Duplicate package ID in release-package manifest: $($package.packageId)"
    }

    if ($package.coordinatedVersionRequired -cne $true) {
        throw "Every currently selected Program Kit package must require the coordinated version: $($package.packageId)"
    }

    if ($allowedRoles -cnotcontains [string] $package.role) {
        throw "Unsupported release-package role for $($package.packageId): $($package.role)"
    }

    $relativeProjectPath = ([string] $package.projectPath).Replace('/', '\')
    if ([IO.Path]::IsPathRooted($relativeProjectPath) -or
        $relativeProjectPath.Contains('..', [StringComparison]::Ordinal)) {
        throw "The project path must be repository-relative and contained: $($package.projectPath)"
    }

    $projectPath = [IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot $relativeProjectPath))
    $sourceRoot = [IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot 'src')).TrimEnd(
            [IO.Path]::DirectorySeparatorChar)
    if (-not $projectPath.StartsWith(
            "$sourceRoot$([IO.Path]::DirectorySeparatorChar)",
            [StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $projectPath -PathType Leaf)) {
        throw "The selected project is absent or outside src: $($package.projectPath)"
    }

    if (-not $projectPaths.Add($projectPath)) {
        throw "Duplicate project path in release-package manifest: $($package.projectPath)"
    }

    $actualPackageId = Get-ProjectPackageId -ProjectPath $projectPath
    if ($actualPackageId -cne $package.packageId) {
        throw "The project PackageId does not match the manifest for $($package.projectPath)."
    }

    $expectedDependencies = @(
        $package.firstPartyDependencies | ForEach-Object { [string] $_ })
    $actualDependencies = @(
        Get-ProjectFirstPartyDependencies -ProjectPath $projectPath)
    if (($expectedDependencies -join "`n") -cne
        ($actualDependencies -join "`n")) {
        throw "The first-party dependency closure drifted for $($package.packageId)."
    }
}

foreach ($package in $packages) {
    foreach ($dependency in @($package.firstPartyDependencies)) {
        if (-not $packageIds.Contains([string] $dependency)) {
            throw "The first-party dependency is absent from the release selection: $dependency"
        }
    }
}

$actualPackableProjects = @(
    Get-ChildItem -LiteralPath (Join-Path $repositoryRoot 'src') `
        -Recurse `
        -Filter '*.csproj' `
        -File |
        ForEach-Object { $_.FullName } |
        Sort-Object)
$selectedProjects = @($projectPaths | Sort-Object)
if (($actualPackableProjects -join "`n") -cne
    ($selectedProjects -join "`n")) {
    throw 'Every packable first-party project must be selected exactly once by the canonical release-package manifest.'
}

$selectedProjectPaths = @(
    $packages |
        ForEach-Object {
            [IO.Path]::GetFullPath(
                (Join-Path $repositoryRoot (
                    ([string] $_.projectPath).Replace('/', '\'))))
        })
$plan = [ordered]@{
    productVersion = [string] $manifest.productVersion
    packageCount = $packages.Count
    invocations = @(
        [ordered]@{
            phase = 'restore'
            executable = 'dotnet'
            arguments = @(
                'restore',
                $solutionPath,
                '--locked-mode',
                '--nologo')
        },
        [ordered]@{
            phase = 'build'
            executable = 'dotnet'
            arguments = @(
                'build',
                $solutionPath,
                '--configuration',
                'Release',
                '--no-restore',
                '-property:ProgramKitAggregatePackReceiptRoot=<transaction-receipts>',
                '--nologo')
        },
        [ordered]@{
            phase = 'aggregate-pack'
            executable = 'dotnet'
            arguments = @(
                'msbuild',
                $packProjectPath,
                '-target:PackManifestSelection',
                '-maxCpuCount:4',
                '-property:Configuration=Release',
                '-property:NoRestore=true',
                '-property:NoBuild=true',
                "-property:ProgramKitExpectedPackageCount=$($packages.Count)",
                '-property:ProgramKitPackageSelectionProps=<transaction-selection-props>',
                '-property:ProgramKitAggregatePackReceiptRoot=<transaction-receipts>',
                '-property:PackageOutputPath=<transaction-staging-feed>')
        })
}
if ($PlanOnly) {
    $plan | ConvertTo-Json -Depth 8
    return
}

$outputParent = Split-Path -Parent $outputPath
if (-not (Test-Path -LiteralPath $outputParent -PathType Container)) {
    throw "The parent of OutputRoot must already exist: $outputParent"
}

$stagePath = Join-Path $outputParent (
    ".program-kit-consumer-feed-$([guid]::NewGuid().ToString('N'))")
$stageFeedPath = Join-Path $stagePath 'feed'
$receiptRootPath = Join-Path $stagePath 'receipts'
$selectionPropsPath = Join-Path $stagePath 'package-selection.props'
try {
    New-Item -ItemType Directory -Path $stageFeedPath | Out-Null
    Write-PackageSelectionProps `
        -Path $selectionPropsPath `
        -Projects $selectedProjectPaths
    Invoke-CheckedDotNet `
        -Phase 'locked restore' `
        -Arguments @(
            'restore',
            $solutionPath,
            '--locked-mode',
            '--nologo')
    Invoke-CheckedDotNet `
        -Phase 'release build' `
        -Arguments @(
            'build',
            $solutionPath,
            '--configuration',
            'Release',
            '--no-restore',
            "-property:ProgramKitAggregatePackReceiptRoot=$receiptRootPath",
            '--nologo')
    Invoke-CheckedDotNet `
        -Phase 'aggregate no-restore/no-build pack' `
        -Arguments @(
            'msbuild',
            $packProjectPath,
            '-target:PackManifestSelection',
            '-maxCpuCount:4',
            '-property:Configuration=Release',
            '-property:NoRestore=true',
            '-property:NoBuild=true',
            "-property:ProgramKitExpectedPackageCount=$($packages.Count)",
            "-property:ProgramKitPackageSelectionProps=$selectionPropsPath",
            "-property:ProgramKitAggregatePackReceiptRoot=$receiptRootPath",
            "-property:PackageOutputPath=$stageFeedPath")

    $actualArchives = @(
        Get-ChildItem -LiteralPath $stageFeedPath -Filter '*.nupkg' -File |
            Sort-Object Name)
    $expectedFilenames = @(
        $packages |
            ForEach-Object {
                "$($_.packageId).$($manifest.productVersion).nupkg"
            } |
            Sort-Object)
    $actualFilenames = @($actualArchives.Name | Sort-Object)
    if (($expectedFilenames -join "`n") -cne
        ($actualFilenames -join "`n")) {
        throw 'The aggregate pack output has missing or extra package archives.'
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $packageEvidence = @()
    foreach ($package in $packages) {
        $filename = "$($package.packageId).$($manifest.productVersion).nupkg"
        $archivePath = Join-Path $stageFeedPath $filename
        $archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
        try {
            $forbidden = @(
                $archive.Entries |
                    Where-Object {
                        $entry = $_.FullName.Replace('\', '/')
                        $entry -match '(^|/)\.contributors/' -or
                        $entry -match '(^|/)bootstrap/' -or
                        $entry -match '(^|/)authoring-workspace\.json$' -or
                        $entry -match '(^|/)(bin|obj|\.git)/'
                    })
            if ($forbidden.Count -ne 0) {
                throw "Package $filename contains forbidden authoring or build-cache content."
            }

            $nuspecEntries = @(
                $archive.Entries |
                    Where-Object {
                        $_.FullName.EndsWith(
                            '.nuspec',
                            [StringComparison]::OrdinalIgnoreCase)
                    })
            if ($nuspecEntries.Count -ne 1) {
                throw "Package $filename must contain exactly one nuspec."
            }

            $reader = [IO.StreamReader]::new(
                $nuspecEntries[0].Open(),
                [Text.UTF8Encoding]::new($false),
                $true)
            try {
                [xml] $nuspec = $reader.ReadToEnd()
            }
            finally {
                $reader.Dispose()
            }

            $metadata = $nuspec.package.metadata
            if ([string] $metadata.id -cne $package.packageId -or
                [string] $metadata.version -cne $manifest.productVersion) {
                throw "Package identity/version drifted inside $filename."
            }

            $firstPartyDependencyEvidence = @()
            $nuspecDependencies = @(
                $metadata.dependencies.dependency) +
                @($metadata.dependencies.group.dependency)
            foreach ($dependency in $nuspecDependencies) {
                if ($null -eq $dependency -or
                    -not ([string] $dependency.id).StartsWith(
                        'Orbyss.ProgramKit.',
                        [StringComparison]::Ordinal)) {
                    continue
                }

                $dependencyVersion = [string] $dependency.version
                if ($dependencyVersion -cne $manifest.productVersion -and
                    $dependencyVersion -cne "[$($manifest.productVersion), )" -and
                    $dependencyVersion -cne "[$($manifest.productVersion)]") {
                    throw "First-party dependency version drifted in ${filename}: $($dependency.id) $dependencyVersion"
                }

                $firstPartyDependencyEvidence += [ordered]@{
                    packageId = [string] $dependency.id
                    versionRange = $dependencyVersion
                }
            }

            $actualDependencyIds = @(
                $firstPartyDependencyEvidence.packageId |
                    Sort-Object -Unique)
            $expectedDependencyIds = if (
                $package.role -ceq 'tool' -or
                $package.role -ceq 'build-integration') {
                @()
            }
            else {
                @(
                    $package.firstPartyDependencies |
                        ForEach-Object { [string] $_ } |
                        Sort-Object -Unique)
            }
            if (($actualDependencyIds -join "`n") -cne
                ($expectedDependencyIds -join "`n")) {
                throw "The packed first-party dependency closure drifted for $($package.packageId)."
            }

            $file = Get-Item -LiteralPath $archivePath
            $packageEvidence += [ordered]@{
                packageId = [string] $package.packageId
                version = [string] $manifest.productVersion
                filename = $filename
                sha256 = Get-Sha256 -Path $archivePath
                size = $file.Length
                role = [string] $package.role
                firstPartyDependencies = @($firstPartyDependencyEvidence)
            }
        }
        finally {
            $archive.Dispose()
        }
    }

    $sourceManifestDigest = Get-Sha256 -Path $manifestPath
    $assetManifest = [ordered]@{
        manifestVersion = '0.1.0-alpha.1'
        productVersion = [string] $manifest.productVersion
        sourcePackageManifestSha256 = $sourceManifestDigest
        packages = @($packageEvidence)
    }
    $assetManifestPath = Join-Path $stagePath 'package-manifest.json'
    $assetManifestJson = $assetManifest | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText(
        $assetManifestPath,
        "$assetManifestJson`n",
        [Text.UTF8Encoding]::new($false))

    $checksumRows = @(
        $packageEvidence |
            ForEach-Object {
                "$($_.sha256.Substring(7))  feed/$($_.filename)"
            })
    $checksumRows += "$(
        (Get-Sha256 -Path $assetManifestPath).Substring(7)
    )  package-manifest.json"
    [IO.File]::WriteAllText(
        (Join-Path $stagePath 'SHA256SUMS'),
        "$(($checksumRows | Sort-Object) -join "`n")`n",
        [Text.UTF8Encoding]::new($false))

    Remove-Item -LiteralPath $selectionPropsPath -Force
    Remove-Item -LiteralPath $receiptRootPath -Recurse -Force
    $publicEntries = @(
        Get-ChildItem -LiteralPath $stagePath -Force |
            ForEach-Object { $_.Name } |
            Sort-Object)
    $expectedPublicEntries = @(
        'feed',
        'package-manifest.json',
        'SHA256SUMS') |
        Sort-Object
    if (($publicEntries -join "`n") -cne
        ($expectedPublicEntries -join "`n")) {
        throw "The public consumer-feed output contains unlisted transaction bytes."
    }

    if (Test-Path -LiteralPath $outputPath) {
        throw "The consumer-feed output appeared during the transaction: $outputPath"
    }

    Move-Item -LiteralPath $stagePath -Destination $outputPath
    Write-Output (
        "Program Kit consumer feed created: version=$(
            $manifest.productVersion) packages=$($packages.Count) output=$outputPath")
}
finally {
    if (Test-Path -LiteralPath $stagePath) {
        $resolvedStage = [IO.Path]::GetFullPath($stagePath)
        $resolvedParent = [IO.Path]::GetFullPath($outputParent).TrimEnd(
            [IO.Path]::DirectorySeparatorChar)
        if (-not $resolvedStage.StartsWith(
                "$resolvedParent$([IO.Path]::DirectorySeparatorChar)",
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean a staging path outside the output parent: $resolvedStage"
        }

        Remove-Item -LiteralPath $resolvedStage -Recurse -Force
    }
}
