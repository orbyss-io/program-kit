[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$selectionPath = Join-Path $PSScriptRoot 'active-owned-schema-migration-selection.json'
$boundaryPath = Join-Path $PSScriptRoot 'version-intent-observation-boundary.json'
$outputPath = Join-Path $PSScriptRoot 'version-intent-inventory.json'

function Get-Digest([string]$relativePath) {
    $path = Join-Path $repoRoot $relativePath
    return 'sha256:' +
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function New-Entry(
    [string]$identity,
    [string]$path,
    [string]$locator,
    [string]$value,
    [string]$intent,
    [bool]$active,
    [Nullable[int]]$ordinal,
    [string]$disposition) {
    return [ordered]@{
        identity = $identity
        ownerId = 'pkid:domain:program-kit:version-governance'
        sourcePath = $path
        sourceLocator = $locator
        currentValue = $value
        sourceDigest = Get-Digest $path
        intent = $intent
        isActive = $active
        ownedRevisionOrdinal = $ordinal
        transitionDisposition = $disposition
    }
}

function Add-Owned(
    [Collections.Generic.List[object]]$entries,
    [string]$identity,
    [string]$path,
    [string]$locator,
    [string]$value,
    [int]$ordinal,
    [string]$disposition) {
    $entries.Add((New-Entry `
        $identity `
        $path `
        $locator `
        $value `
        'owned-artifact-revision' `
        $true `
        $ordinal `
        $disposition))
}

function Add-Product(
    [Collections.Generic.List[object]]$entries,
    [string]$identity,
    [string]$path,
    [string]$locator,
    [string]$value) {
    $entries.Add((New-Entry `
        $identity `
        $path `
        $locator `
        $value `
        'product-release' `
        $true `
        $null `
        'coordinate-product-release'))
}

function Add-External(
    [Collections.Generic.List[object]]$entries,
    [string]$identity,
    [string]$path,
    [string]$locator,
    [string]$value) {
    $entries.Add((New-Entry `
        $identity `
        $path `
        $locator `
        $value `
        'external-selection' `
        $true `
        $null `
        'preserve-external-selection'))
}

$entries = [Collections.Generic.List[object]]::new()
$selection = Get-Content -Raw -LiteralPath $selectionPath | ConvertFrom-Json
foreach ($schema in $selection.entries) {
    Add-Owned `
        $entries `
        $schema.identity `
        $schema.sourcePath `
        '/x-program-kit-version' `
        $schema.sourceVersion `
        $schema.ownedRevisionOrdinal `
        'migrate-owned-revision'
}

$selectedTargets = $selection.entries.targetPath |
    ForEach-Object { $_ } |
    Sort-Object -Unique
$alphaSchemas = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'schemas') `
        -Recurse `
        -Filter '*.schema.json' |
    Where-Object {
        $relative = [IO.Path]::GetRelativePath($repoRoot, $_.FullName).Replace('\', '/')
        $selectedTargets -notcontains $relative
    } |
    ForEach-Object {
        try {
            $document = Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json
        }
        catch {
            return
        }

        if ($document.'x-program-kit-identity' -and
            $document.'x-program-kit-version' -match '^0\.1\.0-alpha\.([1-9][0-9]*)$') {
            [pscustomobject]@{
                identity = $document.'x-program-kit-identity'
                version = $document.'x-program-kit-version'
                ordinal = [int]$Matches[1]
                path = [IO.Path]::GetRelativePath($repoRoot, $_.FullName).Replace('\', '/')
            }
        }
    } |
    Group-Object identity |
    ForEach-Object {
        $_.Group | Sort-Object ordinal -Descending | Select-Object -First 1
    }
foreach ($schema in $alphaSchemas) {
    Add-Owned `
        $entries `
        $schema.identity `
        $schema.path `
        '/x-program-kit-version' `
        $schema.version `
        $schema.ordinal `
        'retain-owned-revision'
}

$catalogs = @(
    @('pkid:catalog:program-kit:architecture-schemas', 'src/Orbyss.ProgramKit.Architecture/Schemas/ArchitectureSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:artifact-schemas', 'src/Orbyss.ProgramKit.Artifacts/Schemas/ArtifactsSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:csharp-build-gate-schemas', 'src/Orbyss.ProgramKit.CSharpBuildGates.Contracts/Contracts/Schemas/CSharpBuildGateSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:dev-container-schemas', 'src/Orbyss.ProgramKit.DevContainers/Contracts/Schemas/DevContainerSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:development-schemas', 'src/Orbyss.ProgramKit.Development/Schemas/DevelopmentSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:dotnet-schemas', 'src/Orbyss.ProgramKit.DotNet/Schemas/DotNetSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.17', 17),
    @('pkid:catalog:program-kit:open-console-schemas', 'src/Orbyss.ProgramKit.OpenConsole/Contracts/Schemas/OpenConsoleSchemaModule.cs', '/Version', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:operations-schemas', 'src/Orbyss.ProgramKit.Operations/Contracts/Schemas/OperationsSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:planning-schemas', 'src/Orbyss.ProgramKit.Planning/Schemas/PlanningSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.3', 3),
    @('pkid:catalog:program-kit:quality-schemas', 'src/Orbyss.ProgramKit.Quality/Schemas/QualitySchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:secret-resolution-schemas', 'src/Orbyss.ProgramKit.SecretResolution/Contracts/Schemas/SecretResolutionSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:serialization-schemas', 'src/Orbyss.ProgramKit.Serialization.JSON/Schemas/SerializationJsonSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:tasks-core-schemas', 'src/Orbyss.ProgramKit.Tasks.Core/Schemas/TasksCoreSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:task-schedule-schemas', 'src/Orbyss.ProgramKit.Tasks.Schedules/Schemas/TaskSchedulesSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1),
    @('pkid:catalog:program-kit:cronos-schedule-schemas', 'src/Orbyss.ProgramKit.Tasks.Schedules.Cronos/Schemas/CronosSchedulesSchemaModule.cs', '/CatalogVersion', '0.1.0-alpha.1', 1)
)
foreach ($catalog in $catalogs) {
    Add-Owned $entries $catalog[0] $catalog[1] $catalog[2] $catalog[3] $catalog[4] 'retain-owned-revision'
}

Add-Owned $entries 'pkid:profile:program-kit:dotnet-target' 'Directory.Build.props' '/Project/PropertyGroup/ProgramKitTargetProfileVersion' '0.1.0-alpha.1' 1 'retain-owned-revision'
Add-Owned $entries 'pkid:profile:program-kit:dotnet-target' 'Directory.Build.targets' '/Project/Target/ValidateProgramKitTargetProfile/Version' '0.1.0-alpha.1' 1 'retain-owned-revision'
Add-Owned $entries 'pkid:schema:program-kit:capability-bundle-manifest' '.agent-capabilities/capability-bundle-manifest.json' '/manifestVersion' '0.1.0-alpha.1' 1 'retain-owned-revision'
Add-Owned $entries 'pkid:schema:program-kit:capability-bundle-manifest' 'src/Orbyss.ProgramKit.CommandLine/Operations/Capabilities/Bundles/CapabilityBundleVerifier.cs' '/ExpectedManifestVersion' '0.1.0-alpha.1' 1 'retain-owned-revision'
Add-Owned $entries 'pkid:policy:program-kit:csharp-source-quality-gate' 'governance/csharp-source-quality-gate.md' '/PolicyVersion' '1.10.0' 10 'migrate-owned-revision'
Add-Owned $entries 'pkid:policy:program-kit:authoring-workspace' '.agent-capabilities/authoring-workspace.json' '/policyVersion' '0.1.0-alpha.1' 1 'retain-owned-revision'
Add-Owned $entries 'pkid:capability:program-kit:design-csharp-build-gate' '.agent-capabilities/capabilities/design-csharp-build-gate/CAPABILITY.md' '/CompatibilityAndVersioning/CanonicalCapabilityVersion' '1.0.0' 1 'migrate-owned-revision'
Add-Owned $entries 'pkid:schema:program-kit:software-change-completion-profile-set' '.agent-capabilities/supporting-resources/completion-profiles/software-change/completion-profile-set-1.0.0.schema.json' '/x-program-kit-version' '1.0.0' 1 'migrate-owned-revision'

$completionPath = '.agent-capabilities/supporting-resources/completion-profiles/software-change/completion-profile-set-1.0.0.json'
Add-Owned $entries 'pkid:completion-profile-set:program-kit:software-change' $completionPath '/version' '1.0.0' 1 'migrate-owned-revision'
Add-Owned $entries 'pkid:manifest:program-kit:software-change-completion-profiles' $completionPath '/manifestVersion' '1.0.0' 1 'migrate-owned-revision'
$completion = Get-Content -Raw -LiteralPath (Join-Path $repoRoot $completionPath) | ConvertFrom-Json
for ($index = 0; $index -lt $completion.profiles.Count; $index++) {
    Add-Owned `
        $entries `
        $completion.profiles[$index].identity `
        $completionPath `
        "/profiles/$index/version" `
        $completion.profiles[$index].version `
        1 `
        'migrate-owned-revision'
}

Add-Product $entries 'pkid:release:program-kit:product' 'Directory.Build.props' '/Project/PropertyGroup/Version' '0.1.0-alpha.2'
Add-Product $entries 'pkid:release:program-kit:product' 'Directory.Build.props' '/Project/PropertyGroup/PackageVersion' '0.1.0-alpha.2'
Add-Product $entries 'pkid:capability-bundle:program-kit:capabilities' '.agent-capabilities/capability-bundle-manifest.json' '/bundleVersion' '0.1.0-alpha.2'
Add-Product $entries 'pkid:release:program-kit:product' '.agent-capabilities/capability-bundle-manifest.json' '/kitVersion' '0.1.0-alpha.2'
Add-Product $entries 'pkid:capability-bundle:program-kit:capabilities' 'src/Orbyss.ProgramKit.CommandLine/Operations/Capabilities/Bundles/CapabilityBundleVerifier.cs' '/ExpectedBundleVersion' '0.1.0-alpha.2'
Add-Product $entries 'pkid:release:program-kit:product' 'src/Orbyss.ProgramKit.CommandLine/Operations/Capabilities/Bundles/CapabilityBundleVerifier.cs' '/ExpectedKitVersion' '0.1.0-alpha.2'
Add-Product $entries 'pkid:release:program-kit:product' 'src/Orbyss.ProgramKit.CommandLine/Operations/DotNet/Refresh/DotNetHostRefreshService.cs' '/CurrentProgramKitVersion' '0.1.0-alpha.2'
Add-Product $entries 'pkid:release:program-kit:product' 'src/Orbyss.ProgramKit.DotNet/Generation/Console/Rendering/DotNetConsoleProjectRenderer.cs' '/GeneratedOutputIntegrityBuildPackageVersion' '0.1.0-alpha.2'
Add-Product $entries 'pkid:release:program-kit:product' 'src/Orbyss.ProgramKit.DotNet/Generation/DotNetHostSourceRenderer.cs' '/GeneratedOutputIntegrityBuildPackageVersion' '0.1.0-alpha.2'

Add-External $entries 'pkid:selection:external:central-packages' 'Directory.Packages.props' '/Project/ItemGroup/PackageVersion' 'exact-central-package-selections'
Add-External $entries 'pkid:selection:external:dotnet-sdk' 'global.json' '/sdk/version' '10.0.302'
Add-External $entries 'pkid:selection:external:mstest-sdk' 'global.json' '/msbuild-sdks/MSTest.Sdk' '4.3.2'
Add-External $entries 'pkid:selection:external:dotnet-sdk' 'Directory.Build.props' '/Project/PropertyGroup/ProgramKitSdkVersion' '10.0.302'
Add-External $entries 'pkid:selection:external:csharp-language' 'Directory.Build.props' '/Project/PropertyGroup/ProgramKitLanguageVersion' '14.0'

$boundaryDigest = Get-Digest 'extensions/alpha-version-transition/version-intent-observation-boundary.json'
$inventory = [ordered]@{
    repositoryRoot = '.'
    sourceRoots = @(
        '.agent-capabilities',
        'Directory.Build.props',
        'Directory.Build.targets',
        'Directory.Packages.props',
        'global.json',
        'governance',
        'schemas',
        'src')
    entries = @($entries | Sort-Object sourcePath, sourceLocator)
    completenessEvidence = @(
        [ordered]@{
            identity = 'pkid:evidence:program-kit:version-intent-observation-boundary'
            version = '0.1.0-alpha.1'
            digest = $boundaryDigest
        })
}
$json = $inventory | ConvertTo-Json -Depth 100
$json = $json.Replace(
    "`r`n",
    "`n",
    [StringComparison]::Ordinal).Replace(
        "`r",
        "`n",
        [StringComparison]::Ordinal) + "`n"
[IO.File]::WriteAllText(
    $outputPath,
    $json,
    [Text.UTF8Encoding]::new($false))
Write-Output "Materialized $($entries.Count) classified active version values."
