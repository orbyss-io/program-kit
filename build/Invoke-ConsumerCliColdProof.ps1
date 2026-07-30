[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $PackageRoot,

    [Parameter(Mandatory = $true)]
    [string] $ConsoleConsumerFixtureRoot,

    [Parameter(Mandatory = $true)]
    [string] $GateDefinitionDraft,

    [Parameter(Mandatory = $true)]
    [string] $DesignFlowFixtureRoot,

    [Parameter(Mandatory = $true)]
    [string] $OutputRoot
)

$ErrorActionPreference = 'Stop'
$releaseManifestPath = Join-Path `
    $PSScriptRoot `
    'program-kit-release-packages.json'
if (-not (Test-Path -LiteralPath $releaseManifestPath -PathType Leaf)) {
    throw "The canonical release-package manifest is absent: $releaseManifestPath"
}

$releaseManifest = [IO.File]::ReadAllText(
    $releaseManifestPath) | ConvertFrom-Json
$version = [string] $releaseManifest.productVersion
$expectedPackages = @($releaseManifest.packages)
if ($expectedPackages.Count -eq 0) {
    throw 'The canonical release-package manifest selects no packages.'
}

$packagePath = [IO.Path]::GetFullPath($PackageRoot)
$consoleFixturePath = [IO.Path]::GetFullPath($ConsoleConsumerFixtureRoot)
$gateDraftPath = [IO.Path]::GetFullPath($GateDefinitionDraft)
$designFlowFixturePath = [IO.Path]::GetFullPath($DesignFlowFixtureRoot)
$outputPath = [IO.Path]::GetFullPath($OutputRoot)
if (-not (Test-Path -LiteralPath $packagePath -PathType Container)) {
    throw "The flat package root does not exist: $packagePath"
}

if (-not (Test-Path -LiteralPath $consoleFixturePath -PathType Container)) {
    throw "The Console consumer fixture root does not exist: $consoleFixturePath"
}

foreach ($requiredFixturePath in @(
        'console-command-sketch.json',
        'inputs/version-map.json',
        'inputs/version-selection.json')) {
    if (-not (Test-Path -LiteralPath (
            Join-Path $consoleFixturePath $requiredFixturePath) -PathType Leaf)) {
        throw "The Console consumer fixture is incomplete: $requiredFixturePath"
    }
}

if (-not (Test-Path -LiteralPath $gateDraftPath -PathType Leaf)) {
    throw "The gate-definition draft does not exist: $gateDraftPath"
}

if (-not (Test-Path -LiteralPath $designFlowFixturePath -PathType Container)) {
    throw "The design-flow fixture root does not exist: $designFlowFixturePath"
}

foreach ($requiredDesignFlowPath in @(
        'architecture-design.json',
        'static-conformance-disposition.json',
        'implementation-plan.json')) {
    if (-not (Test-Path -LiteralPath (
            Join-Path $designFlowFixturePath $requiredDesignFlowPath) -PathType Leaf)) {
        throw "The design-flow fixture is incomplete: $requiredDesignFlowPath"
    }
}

if (Test-Path -LiteralPath $outputPath) {
    throw "The cold-proof output already exists: $outputPath"
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    return "sha256:$((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant())"
}

function Get-BytesSha256 {
    param([Parameter(Mandatory = $true)][byte[]] $Bytes)

    return "sha256:$([Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant())"
}

function Invoke-ProcessBytes {
    param(
        [Parameter(Mandatory = $true)][string] $Executable,
        [Parameter(Mandatory = $true)][string] $WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [string[]] $Arguments,
        [int[]] $AllowedExitCodes = @(0)
    )

    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $Executable
    $start.WorkingDirectory = $WorkingDirectory
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in $Arguments) {
        $start.ArgumentList.Add($argument)
    }

    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    if (-not $process.Start()) {
        throw "The process could not start: $Executable"
    }

    $stdout = [IO.MemoryStream]::new()
    $stderr = [IO.MemoryStream]::new()
    $stdoutCopy = $process.StandardOutput.BaseStream.CopyToAsync($stdout)
    $stderrCopy = $process.StandardError.BaseStream.CopyToAsync($stderr)
    $process.WaitForExit()
    $stdoutCopy.GetAwaiter().GetResult()
    $stderrCopy.GetAwaiter().GetResult()
    $result = [pscustomobject]@{
        ExitCode = $process.ExitCode
        StandardOutput = $stdout.ToArray()
        StandardError = $stderr.ToArray()
    }
    $process.Dispose()
    $stdout.Dispose()
    $stderr.Dispose()
    if ($AllowedExitCodes -notcontains $result.ExitCode) {
        $outputText = [Text.Encoding]::UTF8.GetString($result.StandardOutput)
        $errorText = [Text.Encoding]::UTF8.GetString($result.StandardError)
        throw "$Executable $($Arguments -join ' ') failed with exit code $($result.ExitCode).`n$outputText`n$errorText"
    }

    return $result
}

function Write-NuGetConfiguration {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $FeedRoot
    )

    $externalIds = @(
        'Cronos',
        'Humanizer.Core',
        'Json.More.Net',
        'JsonPointer.Net',
        'JsonSchema.Net',
        'JetBrains.Annotations',
        'CShells',
        'CShells.Abstractions',
        'CShells.AspNetCore',
        'Spectre.Console',
        'Spectre.Console.Cli',
        'Spectre.Console.*',
        'Microsoft.CodeAnalysis.Analyzers',
        'Microsoft.CodeAnalysis.Common',
        'Microsoft.CodeAnalysis.CSharp',
        'Microsoft.Extensions.Configuration.Abstractions',
        'Microsoft.Extensions.DependencyInjection',
        'Microsoft.Extensions.DependencyInjection.Abstractions',
        'Microsoft.Extensions.Diagnostics.Abstractions',
        'Microsoft.Extensions.Diagnostics.HealthChecks',
        'Microsoft.Extensions.Diagnostics.HealthChecks.Abstractions',
        'Microsoft.Extensions.FileProviders.Abstractions',
        'Microsoft.Extensions.Hosting.Abstractions',
        'Microsoft.Extensions.Logging.Abstractions',
        'Microsoft.Extensions.Options',
        'Microsoft.Extensions.Primitives',
        'Microsoft.*',
        'System.*'
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
        $writer.WriteAttributeString('key', 'program-kit-release')
        $writer.WriteAttributeString('value', $FeedRoot)
        $writer.WriteEndElement()
        $writer.WriteStartElement('add')
        $writer.WriteAttributeString('key', 'nuget.org')
        $writer.WriteAttributeString('value', 'https://api.nuget.org/v3/index.json')
        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteStartElement('auditSources')
        $writer.WriteStartElement('clear')
        $writer.WriteEndElement()
        $writer.WriteStartElement('add')
        $writer.WriteAttributeString('key', 'nuget.org')
        $writer.WriteAttributeString('value', 'https://api.nuget.org/v3/index.json')
        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteStartElement('fallbackPackageFolders')
        $writer.WriteStartElement('clear')
        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteStartElement('packageSourceMapping')
        $writer.WriteStartElement('clear')
        $writer.WriteEndElement()
        $writer.WriteStartElement('packageSource')
        $writer.WriteAttributeString('key', 'program-kit-release')
        $writer.WriteStartElement('package')
        $writer.WriteAttributeString('pattern', 'Orbyss.ProgramKit.*')
        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteStartElement('packageSource')
        $writer.WriteAttributeString('key', 'nuget.org')
        foreach ($packageId in $externalIds) {
            $writer.WriteStartElement('package')
            $writer.WriteAttributeString('pattern', $packageId)
            $writer.WriteEndElement()
        }

        $writer.WriteEndElement()
        $writer.WriteEndElement()
        $writer.WriteEndElement()
    }
    finally {
        $writer.Dispose()
    }
}

function Assert-ContainsText {
    param(
        [Parameter(Mandatory = $true)][byte[]] $Bytes,
        [Parameter(Mandatory = $true)][string] $Expected
    )

    $text = [Text.Encoding]::UTF8.GetString($Bytes)
    if (-not $text.Contains($Expected, [StringComparison]::Ordinal)) {
        throw "Expected output text was absent: $Expected"
    }
}

function Write-Utf8Json {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)] $Value,
        [switch] $Compress
    )

    $json = if ($Compress) {
        $Value | ConvertTo-Json -Depth 100 -Compress
    }
    else {
        $Value | ConvertTo-Json -Depth 100
    }
    [IO.File]::WriteAllText(
        $Path,
        "$json`n",
        [Text.UTF8Encoding]::new($false))
}

function Assert-FailedWithoutOutput {
    param(
        [Parameter(Mandatory = $true)] $Result,
        [Parameter(Mandatory = $true)][string] $OutputPath,
        [Parameter(Mandatory = $true)][string] $ExpectedDiagnostic
    )

    if ($Result.ExitCode -eq 0) {
        throw "The negative proof unexpectedly succeeded: $ExpectedDiagnostic"
    }

    $combinedBytes = [byte[]] (
        @($Result.StandardOutput) + @($Result.StandardError))
    $combined = [Text.Encoding]::UTF8.GetString($combinedBytes)
    if (-not $combined.Contains(
            $ExpectedDiagnostic,
            [StringComparison]::Ordinal)) {
        throw "The negative proof omitted $ExpectedDiagnostic."
    }

    if (Test-Path -LiteralPath $OutputPath) {
        throw "A failed operation promoted output: $OutputPath"
    }
}

function Assert-ResultContainsText {
    param(
        [Parameter(Mandatory = $true)] $Result,
        [Parameter(Mandatory = $true)][string] $Expected
    )

    $combinedBytes = [byte[]] (
        @($Result.StandardOutput) + @($Result.StandardError))
    $combined = [Text.Encoding]::UTF8.GetString($combinedBytes)
    if (-not $combined.Contains($Expected, [StringComparison]::Ordinal)) {
        throw "Expected process output text was absent: $Expected"
    }
}

$packages = @(
    Get-ChildItem -LiteralPath $packagePath -Filter '*.nupkg' -File |
        Sort-Object Name)
$expectedFilenames = @(
    $expectedPackages |
        ForEach-Object {
            "$($_.packageId).$version.nupkg"
        } |
        Sort-Object)
$actualFilenames = @($packages.Name | Sort-Object)
if (($expectedFilenames -join "`n") -cne
    ($actualFilenames -join "`n")) {
    throw 'The coordinated flat feed does not match the canonical release-package manifest.'
}

$packageEvidence = @()
foreach ($package in $packages) {
    $packageEvidence += [ordered]@{
        filename = $package.Name
        sha256 = Get-Sha256 -Path $package.FullName
        size = $package.Length
    }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$requiredPackageEntries = [ordered]@{
    'Orbyss.ProgramKit.CommandLine' = @(
        'tools/net10.0/any/DotnetToolSettings.xml',
        'tools/net10.0/any/Orbyss.ProgramKit.CommandLine.dll',
        'tools/net10.0/any/Orbyss.ProgramKit.Architecture.dll',
        'tools/net10.0/any/Orbyss.ProgramKit.DotNet.dll',
        'tools/net10.0/any/Orbyss.ProgramKit.Planning.dll')
    'Orbyss.ProgramKit.CSharpBuildGates.Build' = @(
        'build/Orbyss.ProgramKit.CSharpBuildGates.Build.props',
        'build/Orbyss.ProgramKit.CSharpBuildGates.Build.targets',
        'tools/net10.0/Orbyss.ProgramKit.CSharpBuildGates.Build.dll')
    'Orbyss.ProgramKit.GeneratedOutputIntegrity.Build' = @(
        'build/Orbyss.ProgramKit.GeneratedOutputIntegrity.Build.targets',
        'tools/net10.0/Orbyss.ProgramKit.GeneratedOutputIntegrity.Build.dll')
}
$packageEntryEvidence = @()
foreach ($packageId in $requiredPackageEntries.Keys) {
    $archivePath = Join-Path $packagePath "$packageId.$version.nupkg"
    $archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
    try {
        $entries = @(
            $archive.Entries |
                ForEach-Object { $_.FullName.Replace('\', '/') })
        foreach ($requiredEntry in $requiredPackageEntries[$packageId]) {
            if ($entries -cnotcontains $requiredEntry) {
                throw "Package $packageId omitted required entry $requiredEntry."
            }
        }

        $packageEntryEvidence += [ordered]@{
            packageId = $packageId
            requiredEntries = @($requiredPackageEntries[$packageId])
        }
    }
    finally {
        $archive.Dispose()
    }
}

New-Item -ItemType Directory -Path $outputPath | Out-Null
$consumerRoot = Join-Path $outputPath 'consumer'
$toolPath = Join-Path $outputPath 'tool'
$cacheRoot = Join-Path $outputPath 'nuget-cache'
$dotnetHome = Join-Path $outputPath 'dotnet-home'
$httpCache = Join-Path $outputPath 'http-cache'
$applicationData = Join-Path $outputPath 'application-data'
$localApplicationData = Join-Path $outputPath 'local-application-data'
New-Item -ItemType Directory -Path $consumerRoot,$toolPath,$cacheRoot,$dotnetHome |
    Out-Null
$env:APPDATA = $applicationData
$env:LOCALAPPDATA = $localApplicationData
$env:DOTNET_CLI_HOME = $dotnetHome
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$env:DOTNET_NOLOGO = '1'
$env:NUGET_FALLBACK_PACKAGES = ''
$env:NUGET_HTTP_CACHE_PATH = $httpCache
$env:NUGET_PACKAGES = $cacheRoot

$nugetConfiguration = Join-Path $outputPath 'NuGet.Config'
Write-NuGetConfiguration -Path $nugetConfiguration -FeedRoot $packagePath
$install = Invoke-ProcessBytes `
    -Executable 'dotnet' `
    -WorkingDirectory $outputPath `
    -Arguments @(
        'tool',
        'install',
        'Orbyss.ProgramKit.CommandLine',
        '--tool-path',
        $toolPath,
        '--version',
        $version,
        '--configfile',
        $nugetConfiguration,
        '--no-cache',
        '--verbosity',
        'minimal')
$tool = Join-Path $toolPath 'program-kit'
if ($IsWindows) {
    $tool = "$tool.exe"
}

if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
    throw 'The package-installed program-kit executable is absent.'
}

$help = Invoke-ProcessBytes $tool $consumerRoot @('--help')
Assert-ContainsText $help.StandardOutput "Program Kit $version"
$firstUse = Invoke-ProcessBytes $tool $consumerRoot @()
Assert-ContainsText $firstUse.StandardOutput 'capabilities initialize'
$codex = Invoke-ProcessBytes $tool $consumerRoot @(
    'capabilities', 'initialize',
    '--provider', 'codex',
    '--workspace-root', $consumerRoot)
Assert-ContainsText $codex.StandardOutput 'created=6'
$claude = Invoke-ProcessBytes $tool $consumerRoot @(
    'capabilities', 'initialize',
    '--provider', 'claude',
    '--workspace-root', $consumerRoot)
Assert-ContainsText $claude.StandardOutput 'created=6'
$repeat = Invoke-ProcessBytes $tool $consumerRoot @(
    'capabilities', 'initialize',
    '--provider', 'codex',
    '--workspace-root', $consumerRoot)
Assert-ContainsText $repeat.StandardOutput 'unchanged=12'

$lockPath = Join-Path $consumerRoot '.program-kit/capabilities.lock.json'
$lockBytes = [IO.File]::ReadAllBytes($lockPath)
$lock = [Text.Encoding]::UTF8.GetString($lockBytes) | ConvertFrom-Json
if ($lock.cliVersion -ne $version -or
    @($lock.providers).Count -ne 2 -or
    @($lock.resources).Count -eq 0 -or
    @($lock.resources.resourceId | Sort-Object -Unique).Count -ne
        @($lock.resources).Count) {
    throw 'The initialized workspace lock has incomplete version/provider/resource evidence.'
}

$capabilityEvidence = @()
$capabilities = @(
    $lock.providers[0].capabilities |
        Sort-Object capabilityId)
foreach ($capability in $capabilities) {
    $preflight = Invoke-ProcessBytes $tool $consumerRoot @(
        'capabilities', 'preflight',
        $capability.capabilityId,
        '--workspace-root', $consumerRoot,
        '--format', 'json')
    Assert-ContainsText $preflight.StandardOutput '"state":"ready"'
    $read = Invoke-ProcessBytes $tool $consumerRoot @(
        'capabilities', 'read',
        $capability.capabilityId,
        '--workspace-root', $consumerRoot)
    $digest = Get-BytesSha256 $read.StandardOutput
    if ($digest -ne $capability.canonicalSha256) {
        throw "Capability bytes drifted for $($capability.capabilityId)."
    }

    $capabilityEvidence += [ordered]@{
        capabilityId = $capability.capabilityId
        sha256 = $digest
    }
}

$resourceEvidence = @()
foreach ($resource in @($lock.resources | Sort-Object resourceId)) {
    $read = Invoke-ProcessBytes $tool $consumerRoot @(
        'capabilities', 'read-resource',
        $resource.resourceId,
        '--workspace-root', $consumerRoot)
    $digest = Get-BytesSha256 $read.StandardOutput
    if ($digest -ne $resource.sha256) {
        throw "Supporting-resource bytes drifted for $($resource.resourceId)."
    }

    $resourceEvidence += [ordered]@{
        resourceId = $resource.resourceId
        sha256 = $digest
    }
}

$wrapperPaths = @(
    $lock.providers.capabilities.outputPath |
        Sort-Object -Unique)
foreach ($relativePath in $wrapperPaths) {
    $wrapperPath = Join-Path $consumerRoot $relativePath
    $text = [IO.File]::ReadAllText($wrapperPath)
    if (-not $text.Contains(
            'program-kit capabilities preflight',
            [StringComparison]::Ordinal) -or
        -not $text.Contains(
            'program-kit capabilities read',
            [StringComparison]::Ordinal) -or
        $text.Contains(
            '.agent-capabilities/capabilities/',
            [StringComparison]::Ordinal) -or
        $text.Contains(
            '--program-kit-root',
            [StringComparison]::Ordinal)) {
        throw "A generated provider wrapper is not an exact thin CLI trigger: $relativePath"
    }
}

if (Test-Path -LiteralPath (Join-Path $consumerRoot '.agent-capabilities')) {
    throw 'Canonical capability files were materialized into the consumer workspace.'
}

$schemaList = Invoke-ProcessBytes $tool $consumerRoot @(
    'schemas', 'list', '--format', 'json')
Assert-ContainsText $schemaList.StandardOutput `
    '"canonicalUri":"https://schemas.orbyss.io/program-kit/csharp-build-gates/definition/0.1.0-alpha.2/schema.json"'
$schemaCatalog = [Text.Encoding]::UTF8.GetString(
    $schemaList.StandardOutput) | ConvertFrom-Json
$schemaRead = Invoke-ProcessBytes $tool $consumerRoot @(
    'schemas', 'read',
    'pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.2')
Assert-ContainsText $schemaRead.StandardOutput '"$schema"'
$gateSchemaCatalogEntry = @(
    $schemaCatalog.schemas |
        Where-Object {
            $_.id -ceq 'pkid:schema:program-kit:csharp-build-gate-definition' -and
            $_.version -ceq '0.1.0-alpha.2'
        })
if ($gateSchemaCatalogEntry.Count -ne 1 -or
    (Get-BytesSha256 $schemaRead.StandardOutput) -cne
        $gateSchemaCatalogEntry[0].sha256) {
    throw 'Schema retrieval bytes do not match the registered schema catalog digest.'
}

$tamperedSchemaBytes = [byte[]]::new($schemaRead.StandardOutput.Length)
[Array]::Copy(
    $schemaRead.StandardOutput,
    $tamperedSchemaBytes,
    $schemaRead.StandardOutput.Length)
$tamperedSchemaBytes[$tamperedSchemaBytes.Length - 2] =
    $tamperedSchemaBytes[$tamperedSchemaBytes.Length - 2] -bxor 1
if ((Get-BytesSha256 $tamperedSchemaBytes) -ceq
    $gateSchemaCatalogEntry[0].sha256) {
    throw 'A modified schema unexpectedly matched its registered digest.'
}

$diagnostic = Invoke-ProcessBytes $tool $consumerRoot @(
    'diagnostics', 'explain', 'PKCG005', '--format', 'json')
Assert-ContainsText $diagnostic.StandardOutput `
    '"classification":"program-kit-owned"'
$externalDiagnostic = Invoke-ProcessBytes $tool $consumerRoot @(
    'diagnostics', 'explain', 'CS1002', '--format', 'json')
Assert-ContainsText $externalDiagnostic.StandardOutput `
    '"classification":"unregistered-external"'

$identifierDiagnostic = Invoke-ProcessBytes $tool $consumerRoot @(
    'diagnostics', 'explain', 'PKART001', '--format', 'text')
Assert-ContainsText $identifierDiagnostic.StandardOutput `
    'pkid:approval-record:jtest:jtest-2.0'

$consoleDescription = Invoke-ProcessBytes $tool $consumerRoot @(
    'dotnet', 'describe-console-contract', '--format', 'text')
Assert-ContainsText $consoleDescription.StandardOutput `
    'System.Collections.Immutable.ImmutableArray`1'
$gateDescription = Invoke-ProcessBytes $tool $consumerRoot @(
    'csharp-gate', 'describe-definition', '--format', 'text')
Assert-ContainsText $gateDescription.StandardOutput `
    'ProgramKitVerifyGeneratedProject'
Assert-ContainsText $gateDescription.StandardOutput `
    'cli-tests|... sorts before cli|...'

$designFlowRoot = Join-Path $consumerRoot 'design-flow'
New-Item -ItemType Directory -Path $designFlowRoot | Out-Null
$architectureDocument = [IO.File]::ReadAllText(
    (Join-Path $designFlowFixturePath 'architecture-design.json')) |
        ConvertFrom-Json
$architectureDocument | Add-Member `
    -NotePropertyName '$schema' `
    -NotePropertyValue `
        'https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.3/architecture-design.schema.json' `
    -Force
$architectureDocument.domains[0].identity =
    'pkid:domain:program-kit:version.governance'
$dispositionDocument = [IO.File]::ReadAllText(
    (Join-Path $designFlowFixturePath 'static-conformance-disposition.json')) |
        ConvertFrom-Json
$dispositionDocument | Add-Member `
    -NotePropertyName '$schema' `
    -NotePropertyValue `
        'https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.2/static-conformance-disposition.schema.json' `
    -Force
$dispositionDocument.invariantAllocations[0].identity =
    'pkid:invariant:program-kit:alpha.transition-repository-source'
$planDocument = [IO.File]::ReadAllText(
    (Join-Path $designFlowFixturePath 'implementation-plan.json')) |
        ConvertFrom-Json
$planDocument | Add-Member `
    -NotePropertyName '$schema' `
    -NotePropertyValue `
        'https://schemas.orbyss.io/program-kit/planning/implementation-plan/0.1.0-alpha.4/schema.json' `
    -Force
$planDocument.ownerId = 'pkid:approval-record:jtest:jtest-2.0'
$designFlowDocuments = @(
    [ordered]@{
        Name = 'architecture-design.json'
        Value = $architectureDocument
    },
    [ordered]@{
        Name = 'static-conformance-disposition.json'
        Value = $dispositionDocument
    },
    [ordered]@{
        Name = 'implementation-plan.json'
        Value = $planDocument
    })
$designFlowEvidence = @()
foreach ($document in $designFlowDocuments) {
    $path = Join-Path $designFlowRoot $document.Name
    Write-Utf8Json -Path $path -Value $document.Value
    Invoke-ProcessBytes $tool $consumerRoot @(
        'validate', $path) | Out-Null
    $inspection = Invoke-ProcessBytes $tool $consumerRoot @(
        'artifacts', 'inspect', $path, '--format', 'json')
    Assert-ContainsText $inspection.StandardOutput '"valid":true'
    $designFlowEvidence += [ordered]@{
        filename = $document.Name
        sha256 = Get-Sha256 $path
    }
    Remove-Item -LiteralPath $path -Force
}
Remove-Item -LiteralPath $designFlowRoot -Force

$gateRoot = Join-Path $consumerRoot 'gate'
New-Item -ItemType Directory -Path (
    (Join-Path $gateRoot 'src/Consumer')),
    (Join-Path $gateRoot 'analyzers/Consumer.Analyzers'),
    (Join-Path $gateRoot 'artifacts') | Out-Null
[IO.File]::WriteAllText(
    (Join-Path $gateRoot 'src/Consumer/Consumer.csproj'),
    '<Project />',
    [Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText(
    (Join-Path $gateRoot 'src/Consumer/Service.cs'),
    'namespace Consumer;',
    [Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText(
    (Join-Path $gateRoot 'analyzers/Consumer.Analyzers/Consumer.Analyzers.csproj'),
    '<Project />',
    [Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText(
    (Join-Path $gateRoot 'artifacts/Consumer.Analyzers.dll'),
    'analyzer',
    [Text.UTF8Encoding]::new($false))
$gateDraft = [IO.File]::ReadAllText($gateDraftPath) | ConvertFrom-Json
$gateDraft.analyzerComponents[0].artifact.assemblyDigest =
    Get-Sha256 (Join-Path $gateRoot 'artifacts/Consumer.Analyzers.dll')
$gateDraft.profiles.inputs[0].inventory[0].digest =
    Get-Sha256 (Join-Path $gateRoot 'src/Consumer/Service.cs')
$gateInput = Join-Path $gateRoot 'gate-draft.json'
Write-Utf8Json -Path $gateInput -Value $gateDraft
$gateOne = Join-Path $gateRoot 'gate-one.json'
$gateTwo = Join-Path $gateRoot 'gate-two.json'
Invoke-ProcessBytes $tool $consumerRoot @(
    'csharp-gate', 'materialize-definition',
    $gateInput,
    '--output', $gateOne) | Out-Null
Invoke-ProcessBytes $tool $consumerRoot @(
    'csharp-gate', 'materialize-definition',
    $gateInput,
    '--output', $gateTwo) | Out-Null
if ((Get-Sha256 $gateOne) -ne (Get-Sha256 $gateTwo)) {
    throw 'Gate-definition materialization is not byte-deterministic.'
}

Invoke-ProcessBytes $tool $consumerRoot @(
    'csharp-gate', 'validate-definition',
    $gateOne,
    '--diagnostics', 'json') | Out-Null
$inspect = Invoke-ProcessBytes $tool $consumerRoot @(
    'artifacts', 'inspect',
    $gateOne,
    '--schema',
    'pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.2',
    '--format', 'json')
Assert-ContainsText $inspect.StandardOutput '"valid":true'

$lockIntentPath = Join-Path $gateRoot 'lock-intent.json'
$lockIntent = [ordered]@{
    '$schema' =
        'pkid:schema:program-kit:csharp-gate-lock-intent@0.1.0-alpha.1'
    version = '0.1.0-alpha.1'
    lockIdentity = 'pkid:selection-lock:consumer:software'
    disposition = $gateDraft.disposition
    recipes = @()
    operationRevisions = @(
        [ordered]@{
            identity = 'pkid:operation:program-kit:csharp-gate-verify'
            version = '0.1.0-alpha.1'
            digest = "sha256:$('e' * 64)"
        })
    sdkVersion = '10.0.302'
    compilerRoslynVersion = '5.0.0'
    languageVersion = '14.0.0'
    targetFramework = 'net10.0'
    receiptIdentityNamespace = 'pkid:receipt:consumer:gate'
    localAssets = @(
        [ordered]@{
            kind = 'reference'
            repositoryRelativePath =
                'artifacts/Consumer.Analyzers.dll'
        })
}
Write-Utf8Json -Path $lockIntentPath -Value $lockIntent
$bindRequestPath = Join-Path $gateRoot 'gate-bind-request.json'
$selectionLockPath = Join-Path $gateRoot 'selection-lock.json'
Invoke-ProcessBytes $tool $consumerRoot @(
    'csharp-gate', 'scaffold-lock',
    $gateOne,
    $lockIntentPath,
    '--repository-root', $gateRoot,
    '--output', $bindRequestPath) | Out-Null
Invoke-ProcessBytes $tool $consumerRoot @(
    'csharp-gate', 'bind',
    $bindRequestPath,
    '--output', $selectionLockPath) | Out-Null
$selectionInspection = Invoke-ProcessBytes $tool $consumerRoot @(
    'artifacts', 'inspect',
    $selectionLockPath,
    '--schema',
    'pkid:schema:program-kit:csharp-build-gate-selection-lock@0.1.0-alpha.1',
    '--format', 'json')
Assert-ContainsText $selectionInspection.StandardOutput '"valid":true'

$tamperedBindRequestPath = Join-Path $gateRoot 'gate-bind-request-tampered.json'
$tamperedBindRequest = [IO.File]::ReadAllText(
    $bindRequestPath) | ConvertFrom-Json
$originalInputDigest = [string] $tamperedBindRequest.candidateLock.inputDigest
$replacementNibble = if ($originalInputDigest[7] -ceq '0') { '1' } else { '0' }
$tamperedBindRequest.candidateLock.inputDigest =
    $originalInputDigest.Substring(0, 7) +
    $replacementNibble +
    $originalInputDigest.Substring(8)
Write-Utf8Json `
    -Path $tamperedBindRequestPath `
    -Value $tamperedBindRequest `
    -Compress
$tamperedSelectionLockPath = Join-Path $gateRoot 'tampered-selection-lock.json'
$tamperedBind = Invoke-ProcessBytes `
    -Executable $tool `
    -WorkingDirectory $consumerRoot `
    -Arguments @(
        'csharp-gate', 'bind',
        $tamperedBindRequestPath,
        '--output', $tamperedSelectionLockPath) `
    -AllowedExitCodes @(1, 2)
Assert-FailedWithoutOutput `
    -Result $tamperedBind `
    -OutputPath $tamperedSelectionLockPath `
    -ExpectedDiagnostic 'PKCG'

$consoleInputRequest = Join-Path $consumerRoot 'console-input-request.json'
$secondConsoleInputRequest = Join-Path `
    $consumerRoot `
    'console-input-request-repeat.json'
$consoleSketchPath = Join-Path $consumerRoot 'console-command-sketch.json'
$consumerInputRoot = Join-Path $consumerRoot 'inputs'
$consumerProjectRoot = Join-Path `
    $consumerRoot `
    'src/JTest.Console.Integration'
New-Item -ItemType Directory -Path $consumerInputRoot,$consumerProjectRoot |
    Out-Null
Copy-Item `
    -LiteralPath (Join-Path $consoleFixturePath 'console-command-sketch.json') `
    -Destination $consoleSketchPath
Copy-Item `
    -LiteralPath (Join-Path $consoleFixturePath 'inputs/version-map.json') `
    -Destination (Join-Path $consumerInputRoot 'version-map.json')
Copy-Item `
    -LiteralPath (Join-Path $consoleFixturePath 'inputs/version-selection.json') `
    -Destination (Join-Path $consumerInputRoot 'version-selection.json')
$retrievedProject = Invoke-ProcessBytes $tool $consumerRoot @(
    'capabilities', 'read-resource',
    'dotnet-console-integration-project-example',
    '--workspace-root', $consumerRoot)
$retrievedSource = Invoke-ProcessBytes $tool $consumerRoot @(
    'capabilities', 'read-resource',
    'dotnet-console-integration-source-example',
    '--workspace-root', $consumerRoot)
[IO.File]::WriteAllBytes(
    (Join-Path $consumerProjectRoot 'JTest.Console.Integration.csproj'),
    $retrievedProject.StandardOutput)
[IO.File]::WriteAllBytes(
    (Join-Path $consumerProjectRoot 'ConsoleIntegration.cs'),
    $retrievedSource.StandardOutput)

$consumerProject = Join-Path `
    $consumerProjectRoot `
    'JTest.Console.Integration.csproj'
Invoke-ProcessBytes $tool $consumerRoot @(
    'dotnet', 'scaffold-console-request',
    $consoleSketchPath,
    '--workspace-root', $consumerRoot,
    '--consumer-project',
    'src/JTest.Console.Integration/JTest.Console.Integration.csproj',
    '--output', $consoleInputRequest) | Out-Null
Invoke-ProcessBytes $tool $consumerRoot @(
    'dotnet', 'scaffold-console-request',
    $consoleSketchPath,
    '--workspace-root', $consumerRoot,
    '--consumer-project',
    'src/JTest.Console.Integration/JTest.Console.Integration.csproj',
    '--output', $secondConsoleInputRequest) | Out-Null
if ((Get-Sha256 $consoleInputRequest) -cne
    (Get-Sha256 $secondConsoleInputRequest)) {
    throw 'Console request scaffolding is not byte-deterministic.'
}

$requestInspection = Invoke-ProcessBytes $tool $consumerRoot @(
    'artifacts', 'inspect',
    $consoleInputRequest,
    '--schema',
    'pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.2',
    '--format', 'json')
Assert-ContainsText $requestInspection.StandardOutput '"valid":true'

$requestExample = Invoke-ProcessBytes $tool $consumerRoot @(
    'capabilities', 'read-resource',
    'dotnet-console-input-request-example',
    '--workspace-root', $consumerRoot)
$requestExamplePath = Join-Path $consumerRoot 'console-input-request-example.json'
[IO.File]::WriteAllBytes(
    $requestExamplePath,
    $requestExample.StandardOutput)
$requestExampleInspection = Invoke-ProcessBytes $tool $consumerRoot @(
    'artifacts', 'inspect',
    $requestExamplePath,
    '--schema',
    'pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.2',
    '--format', 'json')
Assert-ContainsText $requestExampleInspection.StandardOutput '"valid":true'

$tamperedRequestPath = Join-Path $consumerRoot 'console-input-request-tampered.json'
$tamperedRequestText = [IO.File]::ReadAllText(
    $consoleInputRequest).Replace(
        '"generatedSymbol":"Run"',
        '"generatedSymbol":false',
        [StringComparison]::Ordinal)
if ($tamperedRequestText -ceq [IO.File]::ReadAllText($consoleInputRequest)) {
    throw 'The strict-reader negative could not locate generatedSymbol.'
}

[IO.File]::WriteAllText(
    $tamperedRequestPath,
    $tamperedRequestText,
    [Text.UTF8Encoding]::new($false))
$tamperedExampleInspection = Invoke-ProcessBytes `
    -Executable $tool `
    -WorkingDirectory $consumerRoot `
    -Arguments @(
        'artifacts', 'inspect',
        $tamperedRequestPath,
        '--schema',
        'pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.2',
        '--format', 'json') `
    -AllowedExitCodes @(0)
Assert-ContainsText $tamperedExampleInspection.StandardOutput '"valid":false'
$tamperedMaterializationRoot = Join-Path `
    $consumerRoot `
    '.program-kit/console-inputs-tampered'
$tamperedMaterialization = Invoke-ProcessBytes `
    -Executable $tool `
    -WorkingDirectory $consumerRoot `
    -Arguments @(
        'dotnet', 'materialize-console-inputs',
        $tamperedRequestPath,
        '--workspace-root', $consumerRoot,
        '--output', $tamperedMaterializationRoot,
        '--build-consumer') `
    -AllowedExitCodes @(1, 2)
Assert-FailedWithoutOutput `
    -Result $tamperedMaterialization `
    -OutputPath $tamperedMaterializationRoot `
    -ExpectedDiagnostic 'PKCIM001'
Assert-ResultContainsText $tamperedMaterialization `
    '/request/binding/operations/0/generatedSymbol'
Assert-ResultContainsText $tamperedMaterialization `
    "Member 'generatedSymbol'"
Assert-ResultContainsText $tamperedMaterialization `
    "expected CLR type 'System.String'"

Invoke-ProcessBytes 'dotnet' $consumerRoot @(
    'restore',
    $consumerProject,
    '--configfile',
    $nugetConfiguration,
    '--no-cache',
    '--verbosity',
    'minimal') | Out-Null

$consoleRoot = Join-Path $consumerRoot '.program-kit/console-inputs'
$materialized = Invoke-ProcessBytes $tool $consumerRoot @(
    'dotnet', 'materialize-console-inputs',
    $consoleInputRequest,
    '--workspace-root', $consumerRoot,
    '--output', $consoleRoot,
    '--build-consumer')
Assert-ContainsText $materialized.StandardOutput 'Console inputs created:'
$materializedAgain = Invoke-ProcessBytes $tool $consumerRoot @(
    'dotnet', 'materialize-console-inputs',
    $consoleInputRequest,
    '--workspace-root', $consumerRoot,
    '--output', $consoleRoot,
    '--build-consumer')
Assert-ContainsText $materializedAgain.StandardOutput 'Console inputs unchanged:'

$shellPath = Join-Path $consoleRoot 'shell.json'
$shell = [IO.File]::ReadAllText($shellPath) | ConvertFrom-Json
$consoleHost = @($shell.hosts | Where-Object { $_.kind -eq 'console' })
if ($consoleHost.Count -ne 1) {
    throw 'The Console fixture must bind exactly one Console host.'
}

$hostIdentity = if ($consoleHost[0].identity -is [string]) {
    $consoleHost[0].identity
}
else {
    $consoleHost[0].identity.value
}

$generated = Join-Path $consumerRoot 'generated-console-host'
$generatedAnchor = "$generated.program-kit-generated-output.anchor.json"
Invoke-ProcessBytes $tool $consumerRoot @(
    'dotnet', 'generate-host', 'console',
    '--shell', $shellPath,
    '--host', $hostIdentity,
    '--artifact-manifest', (Join-Path $consoleRoot 'artifact-manifest.json'),
    '--output', $generated) | Out-Null
foreach ($required in @(
        'GeneratedHost.csproj',
        'shell.lock.json',
        'docs/open-console.json')) {
    if (-not (Test-Path -LiteralPath (Join-Path $generated $required))) {
        throw "Console generation omitted required sealed output: $required"
    }
}

if (-not (Test-Path -LiteralPath $generatedAnchor -PathType Leaf)) {
    throw 'Console generation omitted the sibling generated-output anchor.'
}

$projectReference = [IO.Path]::GetRelativePath(
    $generated,
    $consumerProject).Replace('\', '/')
$generatedProjectPath = Join-Path $generated 'GeneratedHost.csproj'
$generatedProject = [IO.File]::ReadAllText($generatedProjectPath)
if (-not $generatedProject.Contains(
        "Include=`"$projectReference`"",
        [StringComparison]::Ordinal)) {
    throw 'The generated Console host does not reference the selected consumer integration project.'
}

if ($generatedProject.Contains(
        'Orbyss.ProgramKit.csproj',
        [StringComparison]::Ordinal) -or
    $generatedProject.Contains(
        '.agent-capabilities',
        [StringComparison]::Ordinal)) {
    throw 'The generated Console host contains a Program Kit source-tree reference.'
}

Invoke-ProcessBytes $tool $consumerRoot @(
    'dotnet', 'verify-host',
    '--root', $generated) | Out-Null
Invoke-ProcessBytes 'dotnet' $consumerRoot @(
    'restore',
    $generatedProjectPath,
    '--configfile',
    $nugetConfiguration,
    '--no-cache',
    '--verbosity',
    'minimal') | Out-Null
Invoke-ProcessBytes 'dotnet' $consumerRoot @(
    'build',
    $generatedProjectPath,
    '--no-restore',
    '--configuration',
    'Release',
    '--verbosity',
    'minimal') | Out-Null
Invoke-ProcessBytes 'dotnet' $consumerRoot @(
    'msbuild',
    $generatedProjectPath,
    '/t:ProgramKitVerifyGeneratedProject',
    '/restore:false',
    '/property:Configuration=Release',
    '/verbosity:minimal') | Out-Null

$generatedTargetsPath = Join-Path $generated 'Directory.Build.targets'
$generatedTargetsBytes = [IO.File]::ReadAllBytes($generatedTargetsPath)
[IO.File]::AppendAllText(
    $generatedTargetsPath,
    "`n<!-- consumer tamper -->",
    [Text.UTF8Encoding]::new($false))
$tamperedGeneratedTarget = Invoke-ProcessBytes `
    -Executable 'dotnet' `
    -WorkingDirectory $consumerRoot `
    -Arguments @(
        'msbuild',
        $generatedProjectPath,
        '/t:ProgramKitVerifyGeneratedProject',
        '/restore:false',
        '/property:Configuration=Release',
        '/verbosity:minimal') `
    -AllowedExitCodes @(1)
Assert-ResultContainsText $tamperedGeneratedTarget 'PKINT100'
[IO.File]::WriteAllBytes($generatedTargetsPath, $generatedTargetsBytes)
Invoke-ProcessBytes 'dotnet' $consumerRoot @(
    'msbuild',
    $generatedProjectPath,
    '/t:ProgramKitVerifyGeneratedProject',
    '/restore:false',
    '/property:Configuration=Release',
    '/verbosity:minimal') | Out-Null

$consoleMaterializationLock = Join-Path `
    $consoleRoot `
    '.program-kit-console-inputs.lock.json'
$consoleMaterializationLockDocument =
    [IO.File]::ReadAllText($consoleMaterializationLock) |
        ConvertFrom-Json
if (@($consoleMaterializationLockDocument.compilationReferences).Count -lt 2 -or
    @($consoleMaterializationLockDocument.outputs).Count -lt 6) {
    throw 'The Console materialization lock omitted reference or output closure evidence.'
}

$tamperedRelative = $lock.providers[0].capabilities[0].outputPath
$tamperedPath = Join-Path $consumerRoot $tamperedRelative
$tamperedOriginalBytes = [IO.File]::ReadAllBytes($tamperedPath)
[IO.File]::AppendAllText(
    $tamperedPath,
    "`nconsumer-tamper",
    [Text.UTF8Encoding]::new($false))
$tamperedPreflight = Invoke-ProcessBytes `
    -Executable $tool `
    -WorkingDirectory $consumerRoot `
    -Arguments @(
        'capabilities', 'preflight',
        $lock.providers[0].capabilities[0].capabilityId,
        '--workspace-root', $consumerRoot,
        '--format', 'json') `
    -AllowedExitCodes @(0)
Assert-ContainsText $tamperedPreflight.StandardOutput '"state":"setup-required"'
$tamperedRead = Invoke-ProcessBytes `
    -Executable $tool `
    -WorkingDirectory $consumerRoot `
    -Arguments @(
        'capabilities', 'read',
        $lock.providers[0].capabilities[0].capabilityId,
        '--workspace-root', $consumerRoot) `
    -AllowedExitCodes @(1)
[IO.File]::WriteAllBytes($tamperedPath, $tamperedOriginalBytes)
$readyAfterRefresh = Invoke-ProcessBytes $tool $consumerRoot @(
    'capabilities', 'preflight',
    $lock.providers[0].capabilities[0].capabilityId,
    '--workspace-root', $consumerRoot,
    '--format', 'json')
Assert-ContainsText $readyAfterRefresh.StandardOutput '"state":"ready"'

$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$forbiddenText = @(
    $repositoryRoot,
    $repositoryRoot.Replace('\', '/'),
    $consoleFixturePath,
    $consoleFixturePath.Replace('\', '/'),
    $gateDraftPath,
    $gateDraftPath.Replace('\', '/'),
    $designFlowFixturePath,
    $designFlowFixturePath.Replace('\', '/'),
    'JTest.HostInputs',
    '.agent-capabilities/capabilities/')
$textExtensions = @(
    '.config',
    '.cs',
    '.csproj',
    '.json',
    '.lock',
    '.md',
    '.props',
    '.targets',
    '.txt',
    '.xml')
foreach ($file in Get-ChildItem -LiteralPath $consumerRoot -Recurse -File) {
    if ($textExtensions -cnotcontains $file.Extension) {
        continue
    }

    $text = [IO.File]::ReadAllText($file.FullName)
    foreach ($forbidden in $forbiddenText) {
        if ($text.Contains($forbidden, [StringComparison]::OrdinalIgnoreCase)) {
            throw "The isolated consumer leaked forbidden source/test/helper text '$forbidden' in $($file.FullName)."
        }
    }

    if ($file.Extension -ceq '.csproj') {
        [xml] $project = $text
        foreach ($reference in @(
                $project.Project.ItemGroup.ProjectReference)) {
            if ($null -ne $reference -and
                ([string] $reference.Include).Contains(
                    'Orbyss.ProgramKit.',
                    [StringComparison]::OrdinalIgnoreCase)) {
                throw "The isolated consumer contains a Program Kit project reference: $($file.FullName)"
            }
        }
    }
}

$proof = [ordered]@{
    formatVersion = '0.1.0-alpha.1'
    productVersion = $version
    packageCount = $packages.Count
    packages = $packageEvidence
    inspectedPackageEntries = $packageEntryEvidence
    capabilityCount = $capabilityEvidence.Count
    capabilities = $capabilityEvidence
    resourceCount = $resourceEvidence.Count
    resources = $resourceEvidence
    lockSha256 = Get-BytesSha256 $lockBytes
    gateDefinitionSha256 = Get-Sha256 $gateOne
    gateBindRequestSha256 = Get-Sha256 $bindRequestPath
    gateSelectionLockSha256 = Get-Sha256 $selectionLockPath
    designFlowDocuments = $designFlowEvidence
    schemaCatalogSha256 = Get-BytesSha256 $schemaList.StandardOutput
    gateDefinitionSchemaSha256 =
        $gateSchemaCatalogEntry[0].sha256
    consoleRequestSource = 'scaffolded-from-command-sketch'
    consoleSketchSha256 = Get-Sha256 $consoleSketchPath
    consoleRequestSha256 = Get-Sha256 $consoleInputRequest
    consoleRequestExampleSha256 = Get-Sha256 $requestExamplePath
    consoleMaterializationLockSha256 =
        Get-Sha256 $consoleMaterializationLock
    consoleReferenceCount =
        @($consoleMaterializationLockDocument.compilationReferences).Count
    consoleOutputAnchorSha256 = Get-Sha256 $generatedAnchor
    generatedProjectTargetsSha256 = Get-Sha256 $generatedTargetsPath
    providers = @($lock.providers.provider | Sort-Object)
    strictReaderTamperExitCode = $tamperedMaterialization.ExitCode
    gateBindTamperExitCode = $tamperedBind.ExitCode
    generatedTargetTamperExitCode = $tamperedGeneratedTarget.ExitCode
    tamperedWrapperReadExitCode = $tamperedRead.ExitCode
    sourceAndHelperLeakage = 'absent'
}
$proofPath = Join-Path $outputPath 'consumer-cli-cold-proof.json'
[IO.File]::WriteAllText(
    $proofPath,
    ($proof | ConvertTo-Json -Depth 8 -Compress),
    [Text.UTF8Encoding]::new($false))
Write-Output $proofPath
