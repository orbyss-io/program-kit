[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ConsumerSet,

    [Parameter(Mandatory = $true)]
    [string] $PackageManifest,

    [Parameter(Mandatory = $true)]
    [string] $OutputRoot
)

$ErrorActionPreference = 'Stop'

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    return "sha256:$((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant())"
}

function Resolve-BelowRoot {
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [Parameter(Mandatory = $true)][string] $RelativePath
    )

    if ([IO.Path]::IsPathRooted($RelativePath) -or $RelativePath.Contains('\')) {
        throw "Only normalized forward-slash relative paths are accepted: $RelativePath"
    }

    $resolved = [IO.Path]::GetFullPath(
        $RelativePath.Replace('/', [IO.Path]::DirectorySeparatorChar),
        $Root)
    $prefix = $Root.TrimEnd([IO.Path]::DirectorySeparatorChar) +
        [IO.Path]::DirectorySeparatorChar
    if (-not $resolved.Equals(
            $Root,
            [StringComparison]::OrdinalIgnoreCase) -and
        -not $resolved.StartsWith(
            $prefix,
            [StringComparison]::OrdinalIgnoreCase)) {
        throw "A declared path escapes its source root: $RelativePath"
    }

    return $resolved
}

function Write-NuGetConfiguration {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $LocalPackageRoot,
        [Parameter(Mandatory = $true)][string[]] $LocalPackageIds,
        [Parameter(Mandatory = $true)][string[]] $ExternalPackageIds
    )

    $settings = [Xml.XmlWriterSettings]::new()
    $settings.Encoding = [Text.UTF8Encoding]::new($false)
    $settings.Indent = $true
    $settings.NewLineChars = "`n"
    $writer = [Xml.XmlWriter]::Create($Path, $settings)
    try {
        $writer.WriteStartElement('configuration')
        $writer.WriteStartElement('packageSources')
        $writer.WriteStartElement('clear')
        $writer.WriteEndElement()
        $writer.WriteStartElement('add')
        $writer.WriteAttributeString('key', 'first-party')
        $writer.WriteAttributeString('value', $LocalPackageRoot)
        $writer.WriteEndElement()
        $writer.WriteStartElement('add')
        $writer.WriteAttributeString('key', 'nuget.org')
        $writer.WriteAttributeString(
            'value',
            'https://api.nuget.org/v3/index.json')
        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteStartElement('auditSources')
        $writer.WriteStartElement('clear')
        $writer.WriteEndElement()
        $writer.WriteStartElement('add')
        $writer.WriteAttributeString('key', 'nuget.org')
        $writer.WriteAttributeString(
            'value',
            'https://api.nuget.org/v3/index.json')
        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteStartElement('fallbackPackageFolders')
        $writer.WriteStartElement('clear')
        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteStartElement('packageSourceMapping')
        $writer.WriteStartElement('clear')
        $writer.WriteEndElement()
        foreach ($mapping in @(
                [pscustomobject]@{
                    Source = 'first-party'
                    PackageIds = $LocalPackageIds
                },
                [pscustomobject]@{
                    Source = 'nuget.org'
                    PackageIds = $ExternalPackageIds
                })) {
            $writer.WriteStartElement('packageSource')
            $writer.WriteAttributeString('key', $mapping.Source)
            foreach ($packageId in $mapping.PackageIds) {
                $writer.WriteStartElement('package')
                $writer.WriteAttributeString('pattern', $packageId)
                $writer.WriteEndElement()
            }
            $writer.WriteEndElement()
        }
        $writer.WriteEndElement()
        $writer.WriteEndElement()
    }
    finally {
        $writer.Dispose()
    }
}

function Invoke-CheckedDotNet {
    param(
        [Parameter(Mandatory = $true)][string] $WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]] $Arguments
    )

    Push-Location -LiteralPath $WorkingDirectory
    try {
        & dotnet @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "dotnet $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-CheckedExecutable {
    param(
        [Parameter(Mandatory = $true)][string] $WorkingDirectory,
        [Parameter(Mandatory = $true)][string] $Executable,
        [Parameter(Mandatory = $true)][string[]] $Arguments
    )

    Push-Location -LiteralPath $WorkingDirectory
    try {
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Executable $($Arguments -join ' ') failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

$consumerSetPath = [IO.Path]::GetFullPath($ConsumerSet)
$packageManifestPath = [IO.Path]::GetFullPath($PackageManifest)
$outputPath = [IO.Path]::GetFullPath($OutputRoot)
if (Test-Path -LiteralPath $outputPath) {
    throw "The isolated-consumer output already exists: $outputPath"
}

$consumerDocument = Get-Content -LiteralPath $consumerSetPath -Raw |
    ConvertFrom-Json
$packageDocument = Get-Content -LiteralPath $packageManifestPath -Raw |
    ConvertFrom-Json
if ($consumerDocument.'$schema' -ne
        'pkid:schema:program-kit:isolated-consumer-set@1.0.0' -or
    $consumerDocument.version -ne '1.0.0') {
    throw 'The isolated-consumer set has an unsupported schema or version.'
}

$consumerManifestRoot = Split-Path -Parent $consumerSetPath
$consumerSourceRoot = Resolve-BelowRoot `
    -Root $consumerManifestRoot `
    -RelativePath $consumerDocument.sourceRoot
$packageRoot = Split-Path -Parent $packageManifestPath
$localPackages = @($packageDocument.packages)
$externalPackages = @($packageDocument.externalPackages)
$localById = @{}
foreach ($package in $localPackages) {
    if ($localById.ContainsKey($package.packageId)) {
        throw "Duplicate local package ID: $($package.packageId)"
    }

    $packagePath = Resolve-BelowRoot `
        -Root $packageRoot `
        -RelativePath $package.packagePath
    if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf) -or
        (Get-Item -LiteralPath $packagePath).Length -ne $package.size -or
        (Get-Sha256 -Path $packagePath) -ne $package.digest) {
        throw "A local package is missing or hash-drifted: $($package.packageId)"
    }

    $localById.Add($package.packageId, $package)
}

$expectedArchives = @(
    $localPackages |
        ForEach-Object {
            (Resolve-BelowRoot `
                -Root $packageRoot `
                -RelativePath $_.packagePath).ToLowerInvariant()
        })
$actualArchives = @(
    Get-ChildItem -LiteralPath $packageRoot -Filter '*.nupkg' -File |
        ForEach-Object { $_.FullName.ToLowerInvariant() })
if (Compare-Object $expectedArchives $actualArchives) {
    throw 'The package root contains a missing or extra nupkg.'
}

$consumerIds = @{}
$consumerSegments = @{}
foreach ($consumer in @($consumerDocument.consumers)) {
    if ($consumerIds.ContainsKey($consumer.identity)) {
        throw "Duplicate consumer identity: $($consumer.identity)"
    }

    $consumerIds.Add($consumer.identity, $true)
    $consumerSegment = $consumer.identity -replace '[^A-Za-z0-9._-]', '_'
    if ($consumerSegments.ContainsKey($consumerSegment)) {
        throw "Consumer identities collapse to the same filesystem segment: $consumerSegment"
    }

    $consumerSegments.Add($consumerSegment, $consumer.identity)
    $expectedReferences = @($consumer.packageIds)
    foreach ($packageId in $expectedReferences) {
        if (-not $localById.ContainsKey($packageId)) {
            throw "Consumer $($consumer.identity) selects an unlisted local package: $packageId"
        }
    }

    if ($consumer.kind -eq 'project') {
        $sourceProject = Resolve-BelowRoot `
            -Root $consumerSourceRoot `
            -RelativePath $consumer.projectPath
        if (-not (Test-Path -LiteralPath $sourceProject -PathType Leaf)) {
            throw "A consumer project is missing: $($consumer.projectPath)"
        }

        [xml] $projectXml = Get-Content -LiteralPath $sourceProject -Raw
        if ($projectXml.Project.ItemGroup.ProjectReference) {
            throw "Project references are forbidden in isolated consumer $($consumer.identity)."
        }

        $declaredReferences = @(
            $projectXml.Project.ItemGroup.PackageReference |
                ForEach-Object { $_.Include } |
                Where-Object { $_ })
        if (Compare-Object $declaredReferences $expectedReferences) {
            throw "Package references drifted for isolated consumer $($consumer.identity)."
        }
    }
    elseif ($consumer.kind -eq 'tool') {
        if ($consumer.operation -ne 'run' -or
            $expectedReferences.Count -ne 1 -or
            [string]::IsNullOrWhiteSpace($consumer.toolCommand) -or
            @($consumer.toolArguments).Count -eq 0) {
            throw "Tool consumer $($consumer.identity) requires one package, one command, arguments, and run operation."
        }
    }
    else {
        throw "Unsupported isolated consumer kind: $($consumer.kind)"
    }
}

New-Item -ItemType Directory -Path $outputPath | Out-Null
foreach ($sourceItem in Get-ChildItem -LiteralPath $consumerSourceRoot) {
    Copy-Item `
        -LiteralPath $sourceItem.FullName `
        -Destination $outputPath `
        -Recurse
}
$nugetConfiguration = Join-Path $outputPath 'NuGet.Config'
Write-NuGetConfiguration `
    -Path $nugetConfiguration `
    -LocalPackageRoot $packageRoot `
    -LocalPackageIds @($localPackages.packageId | Sort-Object) `
    -ExternalPackageIds @($externalPackages.packageId | Sort-Object)

$proofConsumers = @()
foreach ($consumer in @($consumerDocument.consumers)) {
    $consumerSegment = $consumer.identity -replace '[^A-Za-z0-9._-]', '_'
    $consumerRoot = Join-Path $outputPath ".operation/$consumerSegment"
    $materializationCache = Join-Path $consumerRoot 'materialization-cache'
    $lockedCache = Join-Path $consumerRoot 'locked-cache'
    $env:APPDATA = Join-Path $consumerRoot 'application-data'
    $env:LOCALAPPDATA = Join-Path $consumerRoot 'local-application-data'
    $env:DOTNET_CLI_HOME = Join-Path $consumerRoot 'dotnet-home'
    $env:NUGET_HTTP_CACHE_PATH = Join-Path $consumerRoot 'http-cache'
    $env:NUGET_FALLBACK_PACKAGES = ''
    $env:NUGET_PACKAGES = $materializationCache
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    $env:DOTNET_NOLOGO = '1'
    New-Item -ItemType Directory -Path $materializationCache -Force | Out-Null
    if ($consumer.kind -eq 'project') {
        $projectPath = Resolve-BelowRoot `
            -Root $outputPath `
            -RelativePath $consumer.projectPath
        $projectDirectory = Split-Path -Parent $projectPath
        Invoke-CheckedDotNet `
            -WorkingDirectory $projectDirectory `
            -Arguments @(
                'restore',
                $projectPath,
                '--configfile',
                $nugetConfiguration,
                '--packages',
                $materializationCache,
                '--no-http-cache',
                '--force',
                '--use-lock-file',
                '--force-evaluate',
                '--property:RestoreFallbackFolders=',
                '--property:RestoreIgnoreFailedSources=false',
                '--verbosity',
                'minimal')
    }
    else {
        $materializationToolPath = Join-Path $consumerRoot 'materialization-tools'
        $toolPackage = $localById[$consumer.packageIds[0]]
        Invoke-CheckedDotNet `
            -WorkingDirectory $outputPath `
            -Arguments @(
                'tool',
                'install',
                $toolPackage.packageId,
                '--tool-path',
                $materializationToolPath,
                '--version',
                $toolPackage.packageRevision.version,
                '--configfile',
                $nugetConfiguration,
                '--no-cache',
                '--verbosity',
                'minimal')
    }

    $resolvedMaterializationCache = [IO.Path]::GetFullPath(
        $materializationCache)
    $resolvedConsumerRoot = [IO.Path]::GetFullPath($consumerRoot)
    if (-not $resolvedMaterializationCache.StartsWith(
            $resolvedConsumerRoot + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing cache cleanup outside consumer root: $resolvedMaterializationCache"
    }
    Remove-Item -LiteralPath $resolvedMaterializationCache -Recurse -Force
    if ($consumer.kind -eq 'tool') {
        Remove-Item -LiteralPath $materializationToolPath -Recurse -Force
    }

    $env:NUGET_PACKAGES = $lockedCache
    New-Item -ItemType Directory -Path $lockedCache -Force | Out-Null
    if ($consumer.kind -eq 'project') {
        Invoke-CheckedDotNet `
            -WorkingDirectory $projectDirectory `
            -Arguments @(
                'restore',
                $projectPath,
                '--configfile',
                $nugetConfiguration,
                '--packages',
                $lockedCache,
                '--no-http-cache',
                '--force',
                '--locked-mode',
                '--property:RestoreFallbackFolders=',
                '--property:RestoreIgnoreFailedSources=false',
                '--verbosity',
                'minimal')
        Invoke-CheckedDotNet `
            -WorkingDirectory $projectDirectory `
            -Arguments @(
                'build',
                $projectPath,
                '--configuration',
                'Release',
                '--no-restore',
                '--verbosity',
                'minimal')
        if ($consumer.operation -eq 'run') {
            Invoke-CheckedDotNet `
                -WorkingDirectory $projectDirectory `
                -Arguments @(
                    'run',
                    '--project',
                    $projectPath,
                    '--configuration',
                    'Release',
                    '--no-build',
                    '--no-restore')
        }

        $evidenceKind = 'packages-lock'
        $evidenceDigest = Get-Sha256 -Path (
            Join-Path $projectDirectory 'packages.lock.json')
        $proofProjectPath = $consumer.projectPath
    }
    else {
        $lockedToolPath = Join-Path $consumerRoot 'locked-tools'
        Invoke-CheckedDotNet `
            -WorkingDirectory $outputPath `
            -Arguments @(
                'tool',
                'install',
                $toolPackage.packageId,
                '--tool-path',
                $lockedToolPath,
                '--version',
                $toolPackage.packageRevision.version,
                '--configfile',
                $nugetConfiguration,
                '--no-cache',
                '--verbosity',
                'minimal')
        $toolExecutable = Join-Path $lockedToolPath $consumer.toolCommand
        if ($IsWindows) {
            $toolExecutable = "$toolExecutable.exe"
        }

        Invoke-CheckedExecutable `
            -WorkingDirectory $outputPath `
            -Executable $toolExecutable `
            -Arguments @($consumer.toolArguments)
        $evidenceKind = 'tool-package'
        $evidenceDigest = $toolPackage.digest
        $proofProjectPath = $null
    }

    $proofConsumers += [ordered]@{
        identity = $consumer.identity
        kind = $consumer.kind
        operation = $consumer.operation
        packageIds = @($consumer.packageIds)
        resolutionEvidenceKind = $evidenceKind
        resolutionEvidenceDigest = $evidenceDigest
        projectPath = $proofProjectPath
    }
}

$proof = [ordered]@{
    '$schema' = 'pkid:schema:program-kit:isolated-consumer-proof@1.0.0'
    version = '1.0.0'
    packageRootManifestDigest = Get-Sha256 -Path $packageManifestPath
    consumers = $proofConsumers
}
$proofPath = Join-Path $outputPath 'isolated-consumer-proof.json'
$proofJson = $proof | ConvertTo-Json -Depth 8 -Compress
[IO.File]::WriteAllText(
    $proofPath,
    $proofJson,
    [Text.UTF8Encoding]::new($false))
Write-Output $proofPath
