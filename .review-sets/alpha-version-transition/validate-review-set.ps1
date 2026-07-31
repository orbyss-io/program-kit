param(
    [string] $ExtensionRoot = $PSScriptRoot,
    [switch] $SkipManifest
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $ExtensionRoot '..\..'))
$requiredFiles = @(
    'README.md',
    'design-intent.md',
    'static-conformance-design-basis.json',
    'static-conformance-decision-source.json',
    'static-conformance-disposition.json',
    'program-kit-private-gate-selection-lock.json',
    'approval-authority-source.json',
    'design-plan-approval.json',
    'architecture-design.json',
    'architecture-design.md',
    'implementation-plan.json',
    'implementation-plan.md',
    'materialize-review-set.ps1',
    'validate-review-set.ps1'
)
if (-not $SkipManifest) {
    $requiredFiles += @(
        'validation-report.md',
        'review-manifest.json')
}

function Assert-Condition([bool] $condition, [string] $message) {
    if (-not $condition) {
        throw $message
    }
}

function Get-Digest([string] $path) {
    return (
        Get-FileHash -Algorithm SHA256 -LiteralPath $path
    ).Hash.ToLowerInvariant()
}

function Assert-Reference(
    [object] $reference,
    [string] $identity,
    [string] $version,
    [string] $digest,
    [string] $label
) {
    Assert-Condition (
        $null -ne $reference -and
        $reference.identity -eq $identity -and
        $reference.version -eq $version -and
        $reference.digest -eq ('sha256:' + $digest)
    ) "$label is not the expected exact artifact reference."
}

function Test-Reachable(
    [string] $sourceId,
    [string] $targetId,
    [hashtable] $byId,
    [Collections.Generic.HashSet[string]] $visited
) {
    if (-not $visited.Add($sourceId) -or -not $byId.ContainsKey($sourceId)) {
        return $false
    }

    foreach ($dependency in @($byId[$sourceId].dependsOn)) {
        if ($dependency -eq $targetId) {
            return $true
        }

        if (Test-Reachable $dependency $targetId $byId $visited) {
            return $true
        }
    }

    return $false
}

foreach ($file in $requiredFiles) {
    $path = Join-Path $ExtensionRoot $file
    Assert-Condition (Test-Path -LiteralPath $path -PathType Leaf) (
        "Missing required review artifact '$file'.")
    $bytes = [IO.File]::ReadAllBytes($path)
    Assert-Condition (
        $bytes.Length -lt 3 -or
        -not (
            $bytes[0] -eq 0xEF -and
            $bytes[1] -eq 0xBB -and
            $bytes[2] -eq 0xBF
        )
    ) "Artifact '$file' has a UTF-8 byte-order mark."
    $text = [Text.Encoding]::UTF8.GetString($bytes)
    Assert-Condition (-not $text.Contains("`r")) (
        "Artifact '$file' does not use LF-only line endings.")
}

$jsonFiles = @(
    'static-conformance-design-basis.json',
    'static-conformance-decision-source.json',
    'static-conformance-disposition.json',
    'program-kit-private-gate-selection-lock.json',
    'approval-authority-source.json',
    'design-plan-approval.json',
    'architecture-design.json',
    'implementation-plan.json'
)
if (-not $SkipManifest) {
    $jsonFiles += 'review-manifest.json'
}
foreach ($file in $jsonFiles) {
    Get-Content -LiteralPath (Join-Path $ExtensionRoot $file) -Raw |
        ConvertFrom-Json |
        Out-Null
}

$temporaryRoot = Join-Path `
    ([IO.Path]::GetTempPath()) `
    ('program-kit-review-validation-' + [Guid]::NewGuid().ToString('N'))
$resolvedTempBase = [IO.Path]::GetFullPath(
    [IO.Path]::GetTempPath()).TrimEnd(
        [IO.Path]::DirectorySeparatorChar)
$resolvedTemporaryRoot = [IO.Path]::GetFullPath($temporaryRoot)
Assert-Condition (
    $resolvedTemporaryRoot.StartsWith(
        $resolvedTempBase + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)
) 'Temporary schema validator root is outside the system temporary directory.'

try {
    [void][IO.Directory]::CreateDirectory($resolvedTemporaryRoot)
    $binaryRoot = [IO.Path]::GetFullPath(
        (Join-Path `
            $repositoryRoot `
            'src/Orbyss.ProgramKit.CommandLine/bin/Debug/net10.0'))
    Assert-Condition (
        Test-Path -LiteralPath $binaryRoot -PathType Container
    ) 'The built Program Kit command-line dependency root is unavailable.'
    $program = @'
using System;
using System.Collections.Immutable;
using System.IO;
using System.Linq;
using Orbyss.ProgramKit.Architecture.Schemas;
using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Planning.Schemas;
using Orbyss.ProgramKit.Quality.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

if (args.Length != 4)
{
    Console.Error.WriteLine(
        "Expected architecture, plan, disposition, and approval paths.");
    return 2;
}

var validator = new JsonSchemaWorkbenchValidator(
    new ProgramKitJsonCanonicalizer(),
    new ProgramKitSchemaModuleValidator());

var failures = 0;
failures += Validate(
    args[0],
    new CompositeSchemaModule(
        new ArtifactsSchemaModule(),
        new ArchitectureSchemaModule()),
    "pkid:schema:program-kit:architecture-design",
    "2.0.0");
failures += Validate(
    args[1],
    new CompositeSchemaModule(
        new ArtifactsSchemaModule(),
        new QualitySchemaModule(),
        new PlanningSchemaModule()),
    "pkid:schema:program-kit:implementation-plan",
    "3.0.0");
failures += Validate(
    args[2],
    new CompositeSchemaModule(
        new ArtifactsSchemaModule(),
        new ArchitectureSchemaModule()),
    "pkid:schema:program-kit:static-conformance-disposition",
    "1.0.0");
failures += Validate(
    args[3],
    new CompositeSchemaModule(
        new ArtifactsSchemaModule(),
        new PlanningSchemaModule()),
    "pkid:schema:program-kit:design-plan-approval",
    "1.0.0");
return failures == 0 ? 0 : 1;

int Validate(
    string path,
    IProgramKitSchemaModule module,
    string identity,
    string version)
{
    var resource = module.Resources.Single(candidate =>
        candidate.SchemaReference.Identity.Value == identity &&
        candidate.SchemaReference.Version.Value == version);
    var result = validator.Validate(
        new ReadOnlyMemory<byte>(File.ReadAllBytes(path)),
        module,
        resource.SchemaReference,
        JsonSerializationLimits.Default);
    if (result.IsValid)
    {
        Console.WriteLine($"PASS schema {Path.GetFileName(path)} {identity}@{version}");
        return 0;
    }

    foreach (var diagnostic in result.Diagnostics)
    {
        Console.Error.WriteLine(
            $"FAIL schema {Path.GetFileName(path)} {diagnostic.Id} " +
            $"{diagnostic.Path}: {diagnostic.Message}");
    }

    return 1;
}

sealed class CompositeSchemaModule : IProgramKitSchemaModule
{
    private readonly ImmutableArray<IProgramKitSchemaModule> modules;

    public CompositeSchemaModule(params IProgramKitSchemaModule[] modules)
    {
        this.modules = modules.ToImmutableArray();
        Resources = this.modules
            .SelectMany((module, moduleIndex) =>
                module.Resources.Select(resource =>
                    new ProgramKitSchemaResource(
                        resource.SchemaReference,
                        resource.CanonicalUri,
                        $"{moduleIndex}-{resource.ResourceName}",
                        resource.MediaType,
                        resource.OwnerId,
                        resource.Status,
                        resource.Consumers,
                        resource.Provenance,
                        resource.Compatibility)))
            .ToImmutableArray();
    }

    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:review-validation-schemas");

    public SemanticVersion Version { get; } =
        new("0.1.0-alpha.1");

    public ImmutableArray<ProgramKitSchemaResource> Resources { get; }

    public Stream OpenRead(ArtifactReference schemaReference)
    {
        var module = modules.Single(candidate =>
            candidate.Resources.Any(resource =>
                resource.SchemaReference == schemaReference));
        return module.OpenRead(schemaReference);
    }
}
'@
    $programPath = Join-Path $resolvedTemporaryRoot 'Program.cs'
    [IO.File]::WriteAllText(
        $programPath,
        $program.Replace("`r`n", "`n") + "`n",
        [Text.UTF8Encoding]::new($false))

    $dotnetRoot = Split-Path (Get-Command dotnet).Source -Parent
    $sdkVersion = (& dotnet --version).Trim()
    $compilerPath = Join-Path `
        $dotnetRoot `
        "sdk/$sdkVersion/Roslyn/bincore/csc.dll"
    Assert-Condition (
        Test-Path -LiteralPath $compilerPath -PathType Leaf
    ) 'The .NET C# compiler is unavailable.'
    $referencePackRoot = Join-Path `
        $dotnetRoot `
        'packs/Microsoft.NETCore.App.Ref'
    $referencePackVersion = Get-ChildItem `
        -LiteralPath $referencePackRoot `
        -Directory |
        Where-Object {
            Test-Path -LiteralPath (
                Join-Path $_.FullName 'ref/net10.0')
        } |
        Sort-Object {
            [version]($_.Name.Split('-')[0])
        } -Descending |
        Select-Object -First 1
    Assert-Condition ($null -ne $referencePackVersion) (
        'The .NET 10 reference assembly pack is unavailable.')
    $frameworkReferences = @(
        Get-ChildItem `
            -LiteralPath (
                Join-Path $referencePackVersion.FullName 'ref/net10.0') `
            -Filter '*.dll' |
            Sort-Object Name
    )
    $programKitReferences = @(
        Get-ChildItem -LiteralPath $binaryRoot -Filter '*.dll' |
            Sort-Object Name
    )
    foreach ($reference in $programKitReferences) {
        [IO.File]::Copy(
            $reference.FullName,
            (Join-Path $resolvedTemporaryRoot $reference.Name),
            $true)
    }
    $outputAssembly = Join-Path `
        $resolvedTemporaryRoot `
        'ReviewValidator.dll'
    $compilerArguments = [Collections.Generic.List[string]]::new()
    $compilerArguments.Add($compilerPath)
    $compilerArguments.Add('-nologo')
    $compilerArguments.Add('-target:exe')
    $compilerArguments.Add('-langversion:latest')
    $compilerArguments.Add('-nullable:enable')
    $compilerArguments.Add("-out:$outputAssembly")
    foreach ($reference in @($frameworkReferences + $programKitReferences)) {
        $compilerArguments.Add("-r:$($reference.FullName)")
    }
    $compilerArguments.Add($programPath)
    $compilerOutput = & dotnet @compilerArguments 2>&1
    $compilerExitCode = $LASTEXITCODE
    $compilerOutput | ForEach-Object { Write-Output $_ }
    Assert-Condition ($compilerExitCode -eq 0) (
        "Temporary schema-validator compilation failed with exit code $compilerExitCode.")

    $runtimeVersionLine = & dotnet --list-runtimes |
        Where-Object { $_ -match '^Microsoft\.NETCore\.App 10\.' } |
        Select-Object -Last 1
    Assert-Condition (
        $runtimeVersionLine -match
            '^Microsoft\.NETCore\.App ([0-9]+\.[0-9]+\.[0-9]+)'
    ) 'The .NET 10 runtime is unavailable.'
    $runtimeVersion = $Matches[1]
    $runtimeConfig = [ordered]@{
        runtimeOptions = [ordered]@{
            tfm = 'net10.0'
            framework = [ordered]@{
                name = 'Microsoft.NETCore.App'
                version = $runtimeVersion
            }
        }
    } | ConvertTo-Json -Depth 10
    [IO.File]::WriteAllText(
        (Join-Path $resolvedTemporaryRoot 'ReviewValidator.runtimeconfig.json'),
        $runtimeConfig.Replace("`r`n", "`n") + "`n",
        [Text.UTF8Encoding]::new($false))
    $schemaOutput = & dotnet $outputAssembly `
        (Join-Path $ExtensionRoot 'architecture-design.json') `
        (Join-Path $ExtensionRoot 'implementation-plan.json') `
        (Join-Path $ExtensionRoot 'static-conformance-disposition.json') `
        (Join-Path $ExtensionRoot 'design-plan-approval.json') 2>&1
    $schemaExitCode = $LASTEXITCODE
    $schemaOutput | ForEach-Object { Write-Output $_ }
    Assert-Condition ($schemaExitCode -eq 0) (
        "Backed Program Kit schema validation failed with exit code $schemaExitCode.")
}
finally {
    if (Test-Path -LiteralPath $resolvedTemporaryRoot) {
        Assert-Condition (
            $resolvedTemporaryRoot.StartsWith(
                $resolvedTempBase + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)
        ) 'Refusing temporary cleanup outside the system temporary directory.'
        Remove-Item -LiteralPath $resolvedTemporaryRoot -Recurse -Force
    }
}

$intentPath = Join-Path $ExtensionRoot 'design-intent.md'
$basisPath = Join-Path $ExtensionRoot 'static-conformance-design-basis.json'
$decisionPath = Join-Path `
    $ExtensionRoot `
    'static-conformance-decision-source.json'
$dispositionPath = Join-Path `
    $ExtensionRoot `
    'static-conformance-disposition.json'
$selectionLockPath = Join-Path `
    $ExtensionRoot `
    'program-kit-private-gate-selection-lock.json'
$approvalAuthorityPath = Join-Path `
    $ExtensionRoot `
    'approval-authority-source.json'
$approvalRecordPath = Join-Path `
    $ExtensionRoot `
    'design-plan-approval.json'
$designPath = Join-Path $ExtensionRoot 'architecture-design.json'
$planPath = Join-Path $ExtensionRoot 'implementation-plan.json'
$designMarkdownPath = Join-Path $ExtensionRoot 'architecture-design.md'
$planMarkdownPath = Join-Path $ExtensionRoot 'implementation-plan.md'

$intent = [IO.File]::ReadAllText($intentPath)
$basis = Get-Content -LiteralPath $basisPath -Raw | ConvertFrom-Json
$decision = Get-Content -LiteralPath $decisionPath -Raw | ConvertFrom-Json
$disposition = Get-Content `
    -LiteralPath $dispositionPath `
    -Raw |
    ConvertFrom-Json
$selectionLock = Get-Content `
    -LiteralPath $selectionLockPath `
    -Raw |
    ConvertFrom-Json
$approvalAuthority = Get-Content `
    -LiteralPath $approvalAuthorityPath `
    -Raw |
    ConvertFrom-Json
$approval = Get-Content `
    -LiteralPath $approvalRecordPath `
    -Raw |
    ConvertFrom-Json
$design = Get-Content -LiteralPath $designPath -Raw | ConvertFrom-Json
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$designMarkdown = [IO.File]::ReadAllText($designMarkdownPath)
$planMarkdown = [IO.File]::ReadAllText($planMarkdownPath)
$intentDigest = Get-Digest $intentPath
$basisDigest = Get-Digest $basisPath
$decisionDigest = Get-Digest $decisionPath
$dispositionDigest = Get-Digest $dispositionPath
$selectionLockDigest = Get-Digest $selectionLockPath
$approvalAuthorityDigest = Get-Digest $approvalAuthorityPath
$approvalRecordDigest = Get-Digest $approvalRecordPath
$designDigest = Get-Digest $designPath
$planDigest = Get-Digest $planPath

Assert-Condition (
    $intent.Contains('0.1.0-alpha.2') -and
    $intent.Contains('0.1.0-alpha.3') -and
    -not $intent.Contains('0.1.0.alpha.')
) 'The intent does not use the exact approved SemVer alpha spellings.'
Assert-Condition (
    $decision.decision.disposition -eq 'reuse-existing' -and
    $decision.decision.statement -eq
        'i approve all recommendations and fixes' -and
    @($decision.decision.conditions).Count -eq 0
) 'The static-conformance decision source does not preserve the exact human selection.'
Assert-Reference `
    $basis.intent `
    'pkid:intent:program-kit:alpha-version-transition' `
    '0.1.0-alpha.1' `
    $intentDigest `
    'Static-conformance design-basis intent'
Assert-Reference `
    $decision.designBasis `
    'pkid:design:program-kit:alpha-version-transition-static-basis' `
    '0.1.0-alpha.1' `
    $basisDigest `
    'Static-conformance decision design basis'
Assert-Reference `
    $disposition.softwareDesign `
    'pkid:design:program-kit:alpha-version-transition-static-basis' `
    '0.1.0-alpha.1' `
    $basisDigest `
    'Static-conformance software design basis'
Assert-Reference `
    $disposition.decisionSource.source `
    'pkid:decision-source:program-kit:alpha-version-transition-static-conformance' `
    '0.1.0-alpha.1' `
    $decisionDigest `
    'Static-conformance human decision'
Assert-Condition (
    $disposition.disposition -eq 'reuse-existing' -and
    @($disposition.gateSelections).Count -eq 1 -and
    @($disposition.blockers).Count -eq 0 -and
    $null -eq $disposition.emptySelectionAcceptance
) 'The static-conformance disposition is not one unblocked reuse-existing selection.'
Assert-Reference `
    $disposition.gateSelections[0].gate `
    'pkid:policy:program-kit:csharp-source-quality-gate' `
    '1.10.0' `
    'e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1' `
    'Selected private Program Kit gate'
Assert-Reference `
    $disposition.gateSelections[0].activationMatrix `
    'pkid:activation-matrix:program-kit:private-csharp-gate-build-spine' `
    '1.0.0' `
    'bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b' `
    'Selected private Program Kit activation matrix'
Assert-Reference `
    $selectionLock.disposition `
    'pkid:static-conformance-disposition:program-kit:alpha-version-transition' `
    '1.0.0' `
    $dispositionDigest `
    'Private-gate selection-lock disposition'
Assert-Condition (
    $approvalAuthority.design.digest -eq ('sha256:' + $designDigest) -and
    $approvalAuthority.plan.digest -eq ('sha256:' + $planDigest) -and
    $approvalAuthority.humanDecisionSource.statementSha256 -eq
        'sha256:4eff5d78d4bffe653785d636babca69b75ec50153533a2bd9486decabcadc25b' -and
    $approvalAuthority.humanDecisionSource.decision -eq 'approved' -and
    @($approvalAuthority.humanDecisionSource.conditions).Count -eq 0
) 'The approval authority does not bind the exact design, plan, statement, and unconditional decision.'
Assert-Condition (
    $approval.decision -eq 'approved' -and
    @($approval.conditions).Count -eq 0 -and
    $approval.supersession.state -eq 'active' -and
    $approval.design.digest -eq ('sha256:' + $designDigest) -and
    $approval.plan.digest -eq ('sha256:' + $planDigest) -and
    $approval.authority.source.digest -eq
        ('sha256:' + $approvalAuthorityDigest)
) 'The approval record is not an active unconditional exact-byte approval.'

$intentAuthorities = @(
    $design.sourceTruthAuthorities |
        Where-Object {
            $_.source.identity -eq
                'pkid:intent:program-kit:alpha-version-transition'
        }
)
Assert-Condition ($intentAuthorities.Count -eq 1) (
    'The canonical design must contain one exact human-intent authority.')
Assert-Reference `
    $intentAuthorities[0].source `
    'pkid:intent:program-kit:alpha-version-transition' `
    '0.1.0-alpha.1' `
    $intentDigest `
    'Canonical design intent'
Assert-Reference `
    $design.staticConformanceDisposition `
    'pkid:static-conformance-disposition:program-kit:alpha-version-transition' `
    '1.0.0' `
    $dispositionDigest `
    'Canonical design static-conformance disposition'
Assert-Condition (
    @($design.unresolvedDecisions).Count -eq 0 -and
    @($design.semanticModels).Count -eq 4 -and
    @($design.components).Count -eq 5 -and
    @($design.scenarios).Count -eq 5
) 'The canonical design has unresolved decisions or incomplete transition topology.'
Assert-Condition (
    $design.nonGoals -contains
        'Mutating JTest or any other consumer repository.' -and
    $design.nonGoals -contains
        'Activating Program Kit source capabilities in the Program Kit authoring workspace.'
) 'The canonical design omits a required consumer or capability-isolation non-goal.'

Assert-Reference `
    $plan.design `
    'pkid:design:program-kit:alpha-version-transition' `
    '0.1.0-alpha.1' `
    $designDigest `
    'Implementation-plan design'
Assert-Reference `
    $plan.staticConformanceDisposition `
    'pkid:static-conformance-disposition:program-kit:alpha-version-transition' `
    '1.0.0' `
    $dispositionDigest `
    'Implementation-plan static-conformance disposition'
Assert-Condition (
    $plan.state -eq 'ready-for-human-decision' -and
    @($plan.unresolvedDecisions).Count -eq 0 -and
    $plan.staticConformanceState -eq 'reuse-existing' -and
    $null -eq $plan.gateDesign -and
    $plan.gateDefinition.state -eq 'materialized' -and
    $plan.selectionLock.state -eq 'materialized' -and
    $plan.activationEvidence.state -eq 'materialized' -and
    $plan.selectionLock.integrityDigest -eq
        ('sha256:' + $selectionLockDigest)
) 'The implementation plan does not carry a valid materialized reuse-existing preflight.'

$requirements = @($plan.requirementIds)
$workUnits = @($plan.workUnits)
$trace = @($plan.trace)
Assert-Condition (
    $requirements.Count -eq 14 -and
    @($requirements | Sort-Object -Unique).Count -eq 14
) 'The implementation plan must contain 14 unique requirements.'
Assert-Condition (
    $workUnits.Count -eq 7 -and
    @($workUnits.workUnitId | Sort-Object -Unique).Count -eq 7
) 'The implementation plan must contain 7 unique work units.'
Assert-Condition (
    $trace.Count -eq $requirements.Count -and
    -not (
        Compare-Object `
            ($requirements | Sort-Object) `
            ($trace.requirementId | Sort-Object)
    )
) 'Requirement trace identities do not exactly match requirement identities.'

$workUnitById = @{}
foreach ($workUnit in $workUnits) {
    $workUnitById[$workUnit.workUnitId] = $workUnit
}
foreach ($workUnit in $workUnits) {
    Assert-Condition (
        $workUnit.workUnitKind -ne 'gate-establishment' -and
        $null -ne $workUnit.activationMatrix -and
        $null -ne $workUnit.verificationProfile -and
        @($workUnit.stopConditions).Count -gt 0 -and
        @($workUnit.verification).Count -gt 0 -and
        @($workUnit.compatibility).Count -gt 0
    ) "Work unit '$($workUnit.workUnitId)' lacks its reuse-existing, stop, verification, or compatibility binding."
    foreach ($dependency in @($workUnit.dependsOn)) {
        Assert-Condition $workUnitById.ContainsKey($dependency) (
            "Work unit '$($workUnit.workUnitId)' names unknown dependency '$dependency'.")
        Assert-Condition (
            $workUnitById[$dependency].sequence -lt $workUnit.sequence
        ) "Dependency '$dependency' does not precede '$($workUnit.workUnitId)'."
    }
}
$closure = $workUnitById['PKAV-W070']
Assert-Condition (
    $closure.workUnitKind -eq 'closure'
) 'PKAV-W070 is not the closure work unit.'
foreach ($product in @($workUnits | Where-Object {
    $_.workUnitKind -eq 'product'
})) {
    $visited = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::Ordinal)
    Assert-Condition (
        Test-Reachable $closure.workUnitId $product.workUnitId $workUnitById $visited
    ) "Closure does not depend transitively on '$($product.workUnitId)'."
}
foreach ($entry in $trace) {
    Assert-Condition (@($entry.workUnitIds).Count -gt 0) (
        "Requirement '$($entry.requirementId)' has no work unit.")
    foreach ($workUnitId in @($entry.workUnitIds)) {
        Assert-Condition $workUnitById.ContainsKey($workUnitId) (
            "Requirement '$($entry.requirementId)' names unknown '$workUnitId'.")
    }
}

Assert-Condition (
    $designMarkdown.Contains('Canonical source: `architecture-design.json`') -and
    $designMarkdown.Contains("sha256:$designDigest") -and
    $designMarkdown.Contains('## Version semantic models') -and
    $designMarkdown.Contains('## Approval boundary')
) 'The architecture Markdown projection is stale or incomplete.'
Assert-Condition (
    $planMarkdown.Contains('Canonical source: `implementation-plan.json`') -and
    $planMarkdown.Contains("sha256:$planDigest") -and
    ([regex]::Matches(
        $planMarkdown,
        '(?m)^### `PKAV-W\d{3}`')).Count -eq 7 -and
    $planMarkdown.Contains('## Approval boundary')
) 'The implementation-plan Markdown projection is stale or incomplete.'

if (-not $SkipManifest) {
    $generatedFiles = @(
        'implementation-plan.json',
        'architecture-design.md',
        'implementation-plan.md',
        'review-manifest.json')
    $before = @{}
    foreach ($file in $generatedFiles) {
        $before[$file] = Get-Digest (Join-Path $ExtensionRoot $file)
    }
    & (Join-Path $ExtensionRoot 'materialize-review-set.ps1') |
        Out-Null
    & (Join-Path $ExtensionRoot 'materialize-review-set.ps1') |
        Out-Null
    foreach ($file in $generatedFiles) {
        Assert-Condition (
            $before[$file] -eq
                (Get-Digest (Join-Path $ExtensionRoot $file))
        ) "Materialization is not byte-deterministic for '$file'."
    }

    $manifestPath = Join-Path $ExtensionRoot 'review-manifest.json'
    $manifest = Get-Content `
        -LiteralPath $manifestPath `
        -Raw |
        ConvertFrom-Json
    Assert-Condition (
        $manifest.reviewState -eq 'approved' -and
        $manifest.implementationStatus -eq 'not-started' -and
        $manifest.approvalRecord.sha256 -eq $approvalRecordDigest -and
        $manifest.approvalRecord.authoritySourceSha256 -eq
            $approvalAuthorityDigest -and
        $manifest.approvalBoundary.candidateDesignSha256 -eq $designDigest -and
        $manifest.approvalBoundary.candidatePlanSha256 -eq $planDigest
    ) 'The review manifest has stale approval, implementation, or candidate digest state.'
    foreach ($artifact in @($manifest.artifacts)) {
        $artifactPath = [IO.Path]::GetFullPath(
            (Join-Path $repositoryRoot $artifact.path))
        Assert-Condition (
            $artifactPath.StartsWith(
                $repositoryRoot + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)
        ) "Manifest artifact '$($artifact.path)' escapes the repository."
        Assert-Condition (Test-Path -LiteralPath $artifactPath -PathType Leaf) (
            "Manifest artifact '$($artifact.path)' does not exist.")
        Assert-Condition (
            (Get-Digest $artifactPath) -eq $artifact.sha256
        ) "Manifest digest is stale for '$($artifact.path)'."
    }
}

Write-Output 'PASS files-present-lf-no-bom-and-json-syntax'
Write-Output 'PASS backed-current-contract-schema-validation'
Write-Output 'PASS exact-human-static-conformance-selection'
Write-Output 'PASS version-intent-and-transition-boundaries'
Write-Output 'PASS plan-reuse-existing-graph-trace-and-closure'
Write-Output 'PASS deterministic-markdown-projections'
if (-not $SkipManifest) {
    Write-Output 'PASS deterministic-materialization-and-exact-review-manifest'
}
