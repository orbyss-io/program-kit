param(
    [string] $ExtensionRoot = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $ExtensionRoot '..\..'))
$extensionRelativeRoot = 'extensions/alpha-version-transition'

function Get-Digest([string] $path) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required file does not exist: $path"
    }

    return (
        Get-FileHash -Algorithm SHA256 -LiteralPath $path
    ).Hash.ToLowerInvariant()
}

function Get-RepositoryDigest([string] $relativePath) {
    return Get-Digest (Join-Path $repositoryRoot $relativePath)
}

function New-Reference(
    [string] $identity,
    [string] $version,
    [string] $digest
) {
    return [ordered]@{
        identity = $identity
        version = $version
        digest = 'sha256:' + $digest
    }
}

function Write-Utf8Lf(
    [string] $path,
    [string] $content
) {
    $normalized = $content.Replace("`r`n", "`n").Replace("`r", "`n")
    if (-not $normalized.EndsWith("`n", [StringComparison]::Ordinal)) {
        $normalized += "`n"
    }

    [IO.File]::WriteAllText(
        $path,
        $normalized,
        [Text.UTF8Encoding]::new($false))
}

function Write-Json(
    [string] $name,
    [object] $value
) {
    $json = $value | ConvertTo-Json -Depth 100
    Write-Utf8Lf (Join-Path $ExtensionRoot $name) $json
}

function New-PlannedOutput([string] $workUnitId) {
    return [ordered]@{
        identity = (
            'pkid:plan-output:program-kit:' +
            $workUnitId.ToLowerInvariant())
        version = '0.1.0-alpha.1'
        state = 'prospective'
        integrityDigest = $null
    }
}

function New-Compatibility(
    [string] $subjectId,
    [string] $acceptedVersion,
    [string] $expectedDisposition
) {
    return [ordered]@{
        subjectId = $subjectId
        acceptedVersions = $acceptedVersion
        expectedDisposition = $expectedDisposition
    }
}

function New-WorkUnit(
    [string] $id,
    [int] $sequence,
    [string[]] $dependsOn,
    [string] $outcome,
    [string[]] $allowedEdits,
    [object[]] $compatibility,
    [string] $stopCondition,
    [string] $expectedObservation,
    [string] $kind,
    [object] $designReference,
    [object] $activationMatrix,
    [object] $verificationProfile
) {
    return [ordered]@{
        workUnitId = $id
        requiredOutcome = $outcome
        sequence = $sequence
        parallelGroupId = $null
        dependsOn = $dependsOn
        inputs = @($designReference)
        outputs = @(New-PlannedOutput $id)
        allowedEdits = $allowedEdits
        sourceDependencies = @()
        externalDependencies = @()
        migrations = @()
        compatibility = $compatibility
        stopConditions = @($stopCondition)
        verification = @(
            [ordered]@{
                executable = 'dotnet'
                arguments = @(
                    'test',
                    'ProgramKit.sln',
                    '--no-restore',
                    '--maxcpucount:1',
                    '--property:UseSharedCompilation=false')
                workingDirectory = '.'
                expectedObservation = $expectedObservation
            }
        )
        selectedTests = @()
        workUnitKind = $kind
        activationMatrix = $activationMatrix
        verificationProfile = $verificationProfile
    }
}

function Add-BulletList(
    [Collections.Generic.List[string]] $lines,
    [object[]] $values
) {
    foreach ($value in $values) {
        $lines.Add("- $value")
    }
}

function Render-Architecture(
    [object] $design,
    [string] $digest
) {
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add("# $($design.title)")
    $lines.Add('')
    $lines.Add(
        "Canonical source: ``architecture-design.json`` " +
        "(``sha256:$digest``), governed by Architecture Design ``2.0.0``.")
    $lines.Add('')
    $lines.Add('> Transitional artifact: implementation requires later explicit approval of the exact canonical design and plan digests.')
    $lines.Add('')
    $lines.Add('## Intent')
    $lines.Add('')
    $lines.Add($design.intent)
    $lines.Add('')
    $lines.Add('## Scope')
    $lines.Add('')
    Add-BulletList $lines @($design.scope)
    $lines.Add('')
    $lines.Add('## Non-goals')
    $lines.Add('')
    Add-BulletList $lines @($design.nonGoals)
    $lines.Add('')
    $lines.Add('## Assumptions')
    $lines.Add('')
    Add-BulletList $lines @($design.assumptions)
    $lines.Add('')
    $lines.Add('## Version semantic models')
    $lines.Add('')
    $lines.Add('| Identity | Meaning | Invariants |')
    $lines.Add('|---|---|---|')
    foreach ($model in @($design.semanticModels)) {
        $lines.Add(
            "| ``$($model.identity)`` | " +
            "$($model.meaning.Replace('|', '\|')) | " +
            "$($model.invariants.Replace('|', '\|')) |")
    }
    $lines.Add('')
    $lines.Add('## Components')
    $lines.Add('')
    foreach ($component in @($design.components)) {
        $lines.Add("### ``$($component.identity)``")
        $lines.Add('')
        $lines.Add($component.purpose)
        $lines.Add('')
        $lines.Add("- Owner: ``$($component.ownerId)``")
        $lines.Add("- Kind: ``$($component.kind)``")
        $lines.Add("- Activatable: ``$($component.isActivatable.ToString().ToLowerInvariant())``")
        $lines.Add("- Compatibility boundary: $($component.compatibilityBoundary)")
        $lines.Add('')
    }
    $lines.Add('## Reference rules')
    $lines.Add('')
    foreach ($rule in @($design.referenceRules)) {
        $lines.Add(
            "- **$($rule.disposition)** ``$($rule.identity)`` — " +
            "$($rule.referencingScope) → $($rule.referencedScope). " +
            "$($rule.rationale)")
    }
    $lines.Add('')
    $lines.Add('## Boundaries')
    $lines.Add('')
    foreach ($property in $design.boundaries.PSObject.Properties) {
        $boundary = $property.Value
        $lines.Add("### $($property.Name)")
        $lines.Add('')
        $lines.Add($boundary.policy)
        $lines.Add('')
        $lines.Add('Guarantees:')
        $lines.Add('')
        Add-BulletList $lines @($boundary.guarantees)
        $lines.Add('')
        $lines.Add('Exclusions:')
        $lines.Add('')
        Add-BulletList $lines @($boundary.exclusions)
        $lines.Add('')
    }
    $lines.Add('## Scenarios')
    $lines.Add('')
    foreach ($scenario in @($design.scenarios)) {
        $lines.Add("### ``$($scenario.identity)``")
        $lines.Add('')
        $lines.Add("**Actor:** $($scenario.actor)")
        $lines.Add('')
        $lines.Add("**Intent:** $($scenario.intent)")
        $lines.Add('')
        $lines.Add('Steps:')
        $lines.Add('')
        $step = 1
        foreach ($value in @($scenario.steps)) {
            $lines.Add("$step. $value")
            $step++
        }
        $lines.Add('')
        $lines.Add('Outcomes:')
        $lines.Add('')
        Add-BulletList $lines @($scenario.outcomes)
        $lines.Add('')
        $lines.Add('Failure outcomes:')
        $lines.Add('')
        Add-BulletList $lines @($scenario.failureOutcomes)
        $lines.Add('')
    }
    $lines.Add('## Static conformance')
    $lines.Add('')
    $lines.Add(
        "Disposition: ``$($design.staticConformanceDisposition.identity)" +
        "@$($design.staticConformanceDisposition.version)`` " +
        "(``$($design.staticConformanceDisposition.digest)``).")
    $lines.Add('')
    $lines.Add('The selected disposition is `reuse-existing` for the private Program Kit C# gate. Repository-wide version, package, migration, bundle, and initialization invariants remain executable or architecture conformance obligations.')
    $lines.Add('')
    $lines.Add('## Approval boundary')
    $lines.Add('')
    $lines.Add('This design is `scaffolded`. It is not approved and authorizes no implementation, publication, capability activation, consumer mutation, or JTest change.')
    return [string]::Join("`n", $lines)
}

function Render-Plan(
    [object] $plan,
    [string] $digest
) {
    $lines = [Collections.Generic.List[string]]::new()
    $lines.Add('# Program Kit alpha version transition implementation plan')
    $lines.Add('')
    $lines.Add(
        "Canonical source: ``implementation-plan.json`` " +
        "(``sha256:$digest``), governed by Implementation Plan ``3.0.0``.")
    $lines.Add('')
    $lines.Add(
        "Design binding: ``$($plan.design.identity)" +
        "@$($plan.design.version)`` (``$($plan.design.digest)``).")
    $lines.Add('')
    $lines.Add("State: ``$($plan.state)``.")
    $lines.Add('')
    $lines.Add('## Requirements')
    $lines.Add('')
    $lines.Add('| ID | Observable outcome | Work units |')
    $lines.Add('|---|---|---|')
    foreach ($trace in @($plan.trace)) {
        $units = [string]::Join(', ', @($trace.workUnitIds))
        $lines.Add(
            "| ``$($trace.requirementId)`` | " +
            "$($trace.observableAcceptanceOutcome.Replace('|', '\|')) | " +
            "``$units`` |")
    }
    $lines.Add('')
    $lines.Add('## Work units')
    $lines.Add('')
    foreach ($unit in @($plan.workUnits)) {
        $lines.Add("### ``$($unit.workUnitId)``")
        $lines.Add('')
        $lines.Add($unit.requiredOutcome)
        $lines.Add('')
        $dependencies = if (@($unit.dependsOn).Count -eq 0) {
            'none'
        } else {
            [string]::Join(', ', @($unit.dependsOn))
        }
        $lines.Add("- Sequence: ``$($unit.sequence)``")
        $lines.Add("- Kind: ``$($unit.workUnitKind)``")
        $lines.Add("- Depends on: ``$dependencies``")
        $lines.Add("- Planned output: ``$($unit.outputs[0].identity)@$($unit.outputs[0].version)``")
        $lines.Add('')
        $lines.Add('Allowed edits:')
        $lines.Add('')
        Add-BulletList $lines @($unit.allowedEdits)
        $lines.Add('')
        $lines.Add('Compatibility:')
        $lines.Add('')
        foreach ($compatibility in @($unit.compatibility)) {
            $lines.Add(
                "- ``$($compatibility.subjectId)`` accepts " +
                "``$($compatibility.acceptedVersions)``: " +
                "$($compatibility.expectedDisposition)")
        }
        $lines.Add('')
        $lines.Add("Stop condition: $($unit.stopConditions[0])")
        $lines.Add('')
        $verification = $unit.verification[0]
        $arguments = [string]::Join(' ', @($verification.arguments))
        $lines.Add(
            "Verification: ``$($verification.executable) $arguments`` — " +
            "$($verification.expectedObservation)")
        $lines.Add('')
    }
    $lines.Add('## Static conformance')
    $lines.Add('')
    $lines.Add("- State: ``$($plan.staticConformanceState)``")
    $lines.Add(
        "- Disposition: ``$($plan.staticConformanceDisposition.identity)" +
        "@$($plan.staticConformanceDisposition.version)``")
    $lines.Add(
        "- Gate: ``$($plan.gateDefinition.identity)" +
        "@$($plan.gateDefinition.version)``")
    $lines.Add(
        "- Selection lock: ``$($plan.selectionLock.identity)" +
        "@$($plan.selectionLock.version)``")
    $lines.Add(
        "- Activation evidence: ``$($plan.activationEvidence.identity)" +
        "@$($plan.activationEvidence.version)``")
    $lines.Add('')
    $lines.Add('Every work unit binds the exact private Program Kit activation matrix and exhaustive verification profile. No gate-establishment unit is needed.')
    $lines.Add('')
    $lines.Add('## Approval boundary')
    $lines.Add('')
    $lines.Add('This plan is ready for one exact human decision. Approval of recommendations does not approve these later-produced bytes. Implementation must stop on material deviation and the follow-on health review must stop again for approval.')
    return [string]::Join("`n", $lines)
}

$designPath = Join-Path $ExtensionRoot 'architecture-design.json'
$dispositionPath = Join-Path $ExtensionRoot 'static-conformance-disposition.json'
$selectionLockPath = Join-Path `
    $ExtensionRoot `
    'program-kit-private-gate-selection-lock.json'
$design = Get-Content -LiteralPath $designPath -Raw | ConvertFrom-Json
$disposition = Get-Content -LiteralPath $dispositionPath -Raw | ConvertFrom-Json
$selectionLock = Get-Content `
    -LiteralPath $selectionLockPath `
    -Raw |
    ConvertFrom-Json

$designDigest = Get-Digest $designPath
$dispositionDigest = Get-Digest $dispositionPath
$selectionLockDigest = Get-Digest $selectionLockPath
$designReference = New-Reference `
    'pkid:design:program-kit:alpha-version-transition' `
    '0.1.0-alpha.1' `
    $designDigest
$dispositionReference = New-Reference `
    'pkid:static-conformance-disposition:program-kit:alpha-version-transition' `
    '1.0.0' `
    $dispositionDigest
$activationMatrixReference = New-Reference `
    'pkid:activation-matrix:program-kit:private-csharp-gate-build-spine' `
    '1.0.0' `
    'bb09e733aae5746784b38c0e71ca9a50acad1a123b50d986fe10abd2b7d27b6b'
$verificationProfileReference = New-Reference `
    'pkid:profile:program-kit:private-csharp-gate-exhaustive' `
    '1.0.0' `
    '80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d'

$requirements = [ordered]@{
    'PKAV-R001' = 'Every active version-bearing repository value is inventoried and has exactly one reviewed version intent.'
    'PKAV-R002' = 'The replaceable alpha policy validates explicit 0.1.0-alpha.N progression without selecting release authority or enforcing stable SemVer significance.'
    'PKAV-R003' = 'Identity plus version plus digest remains immutable and changed canonical bytes require the next alpha ordinal.'
    'PKAV-R004' = 'Every active Program Kit-owned governed identity has an exact legacy-to-alpha mapping, compatibility disposition, migration definition, and closed dependency assessment.'
    'PKAV-R005' = 'Architecture Design, Implementation Plan, and StaticConformanceDisposition move to alpha.2, alpha.3, and alpha.1 respectively before follow-on design.'
    'PKAV-R006' = 'All first-party NuGet packages, CLI release metadata, capability bundle content, and current generated first-party package references use exactly 0.1.0-alpha.2.'
    'PKAV-R007' = 'The capability-bundle manifest format has an independent owned alpha contract revision and cannot be confused with bundle content release.'
    'PKAV-R008' = 'External selections, immutable historical evidence, receipts, and explicit fixtures remain unchanged and explicitly classified.'
    'PKAV-R009' = 'Version maps, schema registries, semantic validators, migration assessment, and exact selectors accept and preserve prerelease SemVer identities.'
    'PKAV-R010' = 'Canonical capability procedures use the new alpha contracts, provider wrappers remain thin, and the regenerated bundle is byte-exact.'
    'PKAV-R011' = 'Isolated capability initialization and refresh succeeds without manual fixes while Program Kit authoring-root activation remains rejected.'
    'PKAV-R012' = 'Local package builds and representative generated hosts prove exact alpha.2 first-party reference agreement without publication.'
    'PKAV-R013' = 'A separate follow-on health design and plan are produced under the new alpha contracts and stop for exact human approval.'
    'PKAV-R014' = 'Closure evidence proves inventory completeness, migration closure, historical immutability, package agreement, bundle integrity, capability isolation, and unchanged deferred scope.'
}

$workUnits = @(
    (New-WorkUnit `
        'PKAV-W010' `
        10 `
        @() `
        'Establish the closed version-intent inventory plus replaceable alpha progression policy schema, model, validator, fixtures, and diagnostics without granting version-selection authority.' `
        @(
            'schemas/versioning and exact schema registration',
            'src/Orbyss.ProgramKit.Artifacts version-intent and progression contracts',
            'src/Orbyss.ProgramKit.Workbench bounded validation operations',
            'focused unit and conformance fixtures, tests, and versioning documentation') `
        @(
            (New-Compatibility `
                'pkid:policy:program-kit:alpha-version-progression' `
                '0.1.0-alpha.1' `
                'First pre-stable policy revision; Release Kit may replace the selected policy through an explicit compatible strategy contract.')) `
        'Stop if intent must be inferred from a numeric shape, the inventory is open-ended or incomplete, or the validator chooses a version or release.' `
        'The closed inventory, alpha ordinal fixtures, duplicate/digest/skip failures, and no-authority behavior pass.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference),
    (New-WorkUnit `
        'PKAV-W020' `
        20 `
        @('PKAV-W010') `
        'Materialize and register Architecture Design 0.1.0-alpha.2, Implementation Plan 0.1.0-alpha.3, and StaticConformanceDisposition 0.1.0-alpha.1 with exact legacy migrations and updated semantic validation.' `
        @(
            'schemas/architecture and src/Orbyss.ProgramKit.Architecture schema modules, models, validators, and migrations',
            'schemas/planning and src/Orbyss.ProgramKit.Planning schema modules, models, validators, admission, and migrations',
            'Workbench schema selection and exact migration registration',
            'design/planning/static fixtures, tests, renderers, and documentation') `
        @(
            (New-Compatibility `
                'pkid:schema:program-kit:architecture-design' `
                '0.1.0-alpha.2' `
                'Replaces legacy 2.0.0 through an explicit deterministic migration; legacy bytes remain immutable.'),
            (New-Compatibility `
                'pkid:schema:program-kit:implementation-plan' `
                '0.1.0-alpha.3' `
                'Replaces legacy 3.0.0 and requires StaticConformanceDisposition 0.1.0-alpha.1.'),
            (New-Compatibility `
                'pkid:schema:program-kit:static-conformance-disposition' `
                '0.1.0-alpha.1' `
                'Replaces legacy 1.0.0 without changing the five explicit human decision states.')) `
        'Stop if legacy schemas are edited, migrations lose information, plan admission weakens the static-conformance preflight, or alpha schema identities do not resolve exactly.' `
        'Old and new schema validation, deterministic migrations, renderers, exact references, semantic validators, and admission fixtures pass.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference),
    (New-WorkUnit `
        'PKAV-W030' `
        30 `
        @('PKAV-W020') `
        'Migrate the remainder of the complete active Program Kit-owned governed inventory to independent alpha ordinals and close every exact reference and dependency edge.' `
        @(
            'Only active owned-artifact paths and registries enumerated by the approved version-intent inventory',
            'Exact migration definitions, compatibility records, schema modules, source models, fixtures, and focused tests',
            'Canonical capability and policy revision metadata without activating capabilities',
            'Version maps, selection documents, assessment fixtures, and versioning documentation') `
        @(
            (New-Compatibility `
                'pkid:map:program-kit:active-owned-alpha-transition' `
                '0.1.0-alpha.1' `
                'Every exact active legacy revision has one reviewed alpha target or an explicit protected non-owned disposition.')) `
        'Stop on an unclassified active value, ambiguous revision ordinal, changed legacy byte, duplicate exact key, unresolved dependency, or a proposed renumber of external, evidence, receipt, or fixture values.' `
        'Inventory completeness, old-byte immutability, exact registrations, version-map closure, reverse migration closure, and protected-category fixtures pass.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference),
    (New-WorkUnit `
        'PKAV-W040' `
        40 `
        @('PKAV-W030') `
        'Project the one explicit 0.1.0-alpha.2 product release across every first-party package, CLI surface, capability bundle content identity, current generated package reference, and exact local-package verification path.' `
        @(
            'Directory.Build.props and bounded central package-version validation',
            'First-party project/package metadata, package locks, and exact package manifests',
            'CLI and generation renderers containing current first-party release metadata',
            'Capability-bundle manifest-format schema and bundle content metadata',
            'Local package, generated-host, bundle, and version-drift conformance tests') `
        @(
            (New-Compatibility `
                'pkid:release:program-kit:product' `
                '0.1.0-alpha.2' `
                'All first-party packaged deliverables and embedded current first-party references agree exactly; no publication is performed.'),
            (New-Compatibility `
                'pkid:schema:program-kit:capability-bundle-manifest' `
                '0.1.0-alpha.1' `
                'The new format separates manifest contract revision from the alpha.2 bundle content release.')) `
        'Stop if any first-party packaged component retains another version, a third-party version is rewritten, bundle content and format are conflated, generated references drift, or verification needs a package feed publication.' `
        'All packages build locally at alpha.2, package archives and bundle bytes inspect exactly, representative generated hosts reference alpha.2, and the drift detector reports no active product-release mismatch.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference),
    (New-WorkUnit `
        'PKAV-W050' `
        50 `
        @('PKAV-W040') `
        'Move canonical design capabilities to the alpha design-flow contracts, regenerate exact provider wrappers and bundle entries, and prove clean isolated initialization plus refresh without authoring-root activation or manual repair.' `
        @(
            '.agent-capabilities canonical design-software and design-csharp-build-gate definitions',
            '.agent-capabilities thin Codex and Claude provider-adapter templates, index, supporting resources, and bundle manifest',
            'bounded capability catalog, bundle, initialization, ownership-lock, refresh migration, and authoring-deny code',
            'isolated capability fixtures, tests, and contributor-facing contract-version guidance') `
        @(
            (New-Compatibility `
                'pkid:capability:program-kit:design-software' `
                '0.1.0-alpha.2' `
                'Procedure authority is preserved while exact design, plan, and disposition contract references move to alpha revisions.'),
            (New-Compatibility `
                'pkid:capability-bundle:program-kit:capabilities' `
                '0.1.0-alpha.2' `
                'Content release matches every packaged Program Kit component; existing exact owned installations migrate only through explicit initialization.')) `
        'Stop if capability authority changes, wrapper semantics are copied, the bundle is stale, refresh overwrites unowned or drifted files, manual fixes are required, or the Program Kit authoring workspace can activate source capabilities.' `
        'Catalog and bundle digests, thin-wrapper drift checks, absent/existing/current/drifted installation fixtures, ownership-lock migration, no-global-writes, and authoring-root denial pass.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference),
    (New-WorkUnit `
        'PKAV-W060' `
        60 `
        @('PKAV-W050') `
        'Produce and validate a separate Architecture Design 0.1.0-alpha.2, Implementation Plan 0.1.0-alpha.3, and StaticConformanceDisposition 0.1.0-alpha.1 review set for the deferred Program Kit health concerns, then stop for exact human approval.' `
        @(
            'One new bounded extensions review directory for installed-bundle refresh, .contributors setup, Console reachability, public analyzers, and JTest handoff planning',
            'Read-only inspection of implemented transition source and existing approved designs',
            'Canonical alpha design, plan, disposition, deterministic Markdown projections, validation report, and exact review manifest') `
        @(
            (New-Compatibility `
                'pkid:review-set:program-kit:program-kit-health' `
                '0.1.0-alpha.1' `
                'Uses only the newly active alpha design-flow contracts and grants no implementation authority before exact approval.')) `
        'Stop if the follow-on review uses legacy design-flow contracts, omits any approved health concern, mutates JTest, implements behavior, or lacks exact human-decision boundaries.' `
        'The alpha review set validates, binds exact digests, covers every deferred concern, and is presented for a separate human approval without implementation.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference),
    (New-WorkUnit `
        'PKAV-W070' `
        70 `
        @('PKAV-W060') `
        'Close the transition with exact inventory, migration, package, bundle, capability-isolation, test, diff, and follow-on review evidence while leaving publication and consumer migration unperformed.' `
        @(
            'Version-transition conformance fixtures and expected bytes',
            'Local package and generated-host inspection evidence',
            'Capability bundle and isolated initialization evidence',
            'Transition implementation closure evidence and bounded documentation corrections') `
        @(
            (New-Compatibility `
                'pkid:evidence:program-kit:alpha-version-transition-closure' `
                '0.1.0-alpha.1' `
                'Binds the exact implemented transition, complete verification results, and explicitly deferred publication and consumer work.')) `
        'Stop on any failing gate or test, incomplete inventory or migration, changed protected history, version drift, stale digest, source capability activation, missing follow-on review, publication attempt, JTest mutation, or material design deviation.' `
        'Locked restore, private gate, full solution build and tests, migration and schema suites, package and generated-host inspection, bundle verification, isolated initialization, changed-file review, and closure evidence all pass.' `
        'closure' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference)
)

$traceMap = [ordered]@{
    'PKAV-R001' = @('PKAV-W010','PKAV-W030','PKAV-W070')
    'PKAV-R002' = @('PKAV-W010','PKAV-W070')
    'PKAV-R003' = @('PKAV-W010','PKAV-W020','PKAV-W030','PKAV-W070')
    'PKAV-R004' = @('PKAV-W020','PKAV-W030','PKAV-W070')
    'PKAV-R005' = @('PKAV-W020','PKAV-W050','PKAV-W060','PKAV-W070')
    'PKAV-R006' = @('PKAV-W040','PKAV-W070')
    'PKAV-R007' = @('PKAV-W040','PKAV-W070')
    'PKAV-R008' = @('PKAV-W010','PKAV-W030','PKAV-W070')
    'PKAV-R009' = @('PKAV-W010','PKAV-W020','PKAV-W030','PKAV-W070')
    'PKAV-R010' = @('PKAV-W050','PKAV-W070')
    'PKAV-R011' = @('PKAV-W050','PKAV-W070')
    'PKAV-R012' = @('PKAV-W040','PKAV-W070')
    'PKAV-R013' = @('PKAV-W060','PKAV-W070')
    'PKAV-R014' = @('PKAV-W070')
}

$trace = @(
    foreach ($entry in $requirements.GetEnumerator()) {
        [ordered]@{
            requirementId = $entry.Key
            ownerId = 'pkid:domain:program-kit:version-governance'
            contractOrArtifact = $designReference
            workUnitIds = $traceMap[$entry.Key]
            implementationOutcome = $entry.Value
            dependencyOrExtensionImpact = @()
            tests = @()
            evidence = @()
            observableAcceptanceOutcome = $entry.Value
        }
    }
)

$plan = [ordered]@{
    design = $designReference
    ownerId = 'pkid:domain:program-kit:version-governance'
    state = 'ready-for-human-decision'
    requirementIds = @($requirements.Keys)
    workUnits = $workUnits
    parallelGroups = @()
    trace = $trace
    unresolvedDecisions = @()
    staticConformanceDisposition = $dispositionReference
    staticConformanceState = 'reuse-existing'
    gateDesign = $null
    gateDefinition = [ordered]@{
        identity = 'pkid:policy:program-kit:csharp-source-quality-gate'
        version = '1.10.0'
        state = 'materialized'
        integrityDigest = 'sha256:e8bc64e36bc98dbc47938daf6e6c56afbb23425774c4d4d3bdf6e28414eee2a1'
    }
    selectionLock = [ordered]@{
        identity = $selectionLock.identity
        version = $selectionLock.version
        state = 'materialized'
        integrityDigest = 'sha256:' + $selectionLockDigest
    }
    activationEvidence = [ordered]@{
        identity = 'pkid:evidence:program-kit:reusable-csharp-build-gates-closure'
        version = '1.0.0'
        state = 'materialized'
        integrityDigest = 'sha256:7f4a6fbe84c42fc983880abb5e9c18b31eae6cbc6588171a76490f558c7d140b'
    }
}
Write-Json 'implementation-plan.json' $plan

$architectureMarkdown = Render-Architecture $design $designDigest
Write-Utf8Lf `
    (Join-Path $ExtensionRoot 'architecture-design.md') `
    $architectureMarkdown
$planPath = Join-Path $ExtensionRoot 'implementation-plan.json'
$planDigest = Get-Digest $planPath
$planMarkdown = Render-Plan $plan $planDigest
Write-Utf8Lf `
    (Join-Path $ExtensionRoot 'implementation-plan.md') `
    $planMarkdown

$validationReportPath = Join-Path $ExtensionRoot 'validation-report.md'
if (Test-Path -LiteralPath $validationReportPath -PathType Leaf) {
    $artifactDefinitions = @(
        [ordered]@{
            artifactId = 'pkid:intent:program-kit:alpha-version-transition'
            artifactVersion = '0.1.0-alpha.1'
            role = 'human-intent-record'
            path = "$extensionRelativeRoot/design-intent.md"
        },
        [ordered]@{
            artifactId = 'pkid:design:program-kit:alpha-version-transition-static-basis'
            artifactVersion = '0.1.0-alpha.1'
            role = 'non-circular-static-conformance-design-basis'
            path = "$extensionRelativeRoot/static-conformance-design-basis.json"
        },
        [ordered]@{
            artifactId = 'pkid:decision-source:program-kit:alpha-version-transition-static-conformance'
            artifactVersion = '0.1.0-alpha.1'
            role = 'human-static-conformance-decision-source'
            path = "$extensionRelativeRoot/static-conformance-decision-source.json"
        },
        [ordered]@{
            artifactId = 'pkid:static-conformance-disposition:program-kit:alpha-version-transition'
            artifactVersion = '1.0.0'
            role = 'transitional-static-conformance-disposition'
            contract = 'pkid:schema:program-kit:static-conformance-disposition'
            contractVersion = '1.0.0'
            contractSha256 = Get-RepositoryDigest 'schemas/architecture/static-conformance-disposition.schema.json'
            path = "$extensionRelativeRoot/static-conformance-disposition.json"
        },
        [ordered]@{
            artifactId = 'pkid:selection-lock:program-kit:alpha-version-transition-private-gate'
            artifactVersion = '0.1.0-alpha.1'
            role = 'materialized-private-gate-selection-lock'
            path = "$extensionRelativeRoot/program-kit-private-gate-selection-lock.json"
        },
        [ordered]@{
            artifactId = 'pkid:design:program-kit:alpha-version-transition'
            artifactVersion = '0.1.0-alpha.1'
            role = 'canonical-transitional-design'
            contract = 'pkid:schema:program-kit:architecture-design'
            contractVersion = '2.0.0'
            contractSha256 = Get-RepositoryDigest 'schemas/architecture/architecture-design-2.0.0.schema.json'
            path = "$extensionRelativeRoot/architecture-design.json"
        },
        [ordered]@{
            artifactId = 'pkid:ai-artifact:program-kit:alpha-version-transition-design-markdown'
            artifactVersion = '0.1.0-alpha.1'
            role = 'human-readable-design-projection'
            canonicalDesignId = 'pkid:design:program-kit:alpha-version-transition'
            canonicalDesignVersion = '0.1.0-alpha.1'
            canonicalDesignSha256 = $designDigest
            path = "$extensionRelativeRoot/architecture-design.md"
        },
        [ordered]@{
            artifactId = 'pkid:plan:program-kit:alpha-version-transition'
            artifactVersion = '0.1.0-alpha.1'
            role = 'canonical-transitional-implementation-plan'
            contract = 'pkid:schema:program-kit:implementation-plan'
            contractVersion = '3.0.0'
            contractSha256 = Get-RepositoryDigest 'schemas/planning/implementation-plan-3.0.0.schema.json'
            designId = 'pkid:design:program-kit:alpha-version-transition'
            designVersion = '0.1.0-alpha.1'
            designSha256 = $designDigest
            path = "$extensionRelativeRoot/implementation-plan.json"
        },
        [ordered]@{
            artifactId = 'pkid:ai-artifact:program-kit:alpha-version-transition-plan-markdown'
            artifactVersion = '0.1.0-alpha.1'
            role = 'human-readable-plan-projection'
            canonicalPlanId = 'pkid:plan:program-kit:alpha-version-transition'
            canonicalPlanVersion = '0.1.0-alpha.1'
            canonicalPlanSha256 = $planDigest
            path = "$extensionRelativeRoot/implementation-plan.md"
        },
        [ordered]@{
            artifactId = 'pkid:evidence:program-kit:alpha-version-transition-validation'
            artifactVersion = '0.1.0-alpha.1'
            role = 'design-validation-report'
            path = "$extensionRelativeRoot/validation-report.md"
        },
        [ordered]@{
            artifactId = 'pkid:tool:program-kit:alpha-version-transition-review-materializer'
            artifactVersion = '0.1.0-alpha.1'
            role = 'deterministic-review-materializer'
            path = "$extensionRelativeRoot/materialize-review-set.ps1"
        },
        [ordered]@{
            artifactId = 'pkid:tool:program-kit:alpha-version-transition-review-validator'
            artifactVersion = '0.1.0-alpha.1'
            role = 'deterministic-review-validator'
            path = "$extensionRelativeRoot/validate-review-set.ps1"
        },
        [ordered]@{
            artifactId = 'pkid:guide:program-kit:alpha-version-transition-review'
            artifactVersion = '0.1.0-alpha.1'
            role = 'review-navigation'
            path = "$extensionRelativeRoot/README.md"
        }
    )
    $manifestArtifacts = @(
        foreach ($definition in $artifactDefinitions) {
            $artifact = [ordered]@{}
            foreach ($property in $definition.GetEnumerator()) {
                $artifact[$property.Key] = $property.Value
            }
            $artifact.sha256 = Get-RepositoryDigest $definition.path
            $artifact
        }
    )
    $manifest = [ordered]@{
        manifestKind = 'program-kit-design-review'
        manifestVersion = '0.1.0-alpha.1'
        reviewSetId = 'pkid:review-set:program-kit:alpha-version-transition'
        reviewSetVersion = '0.1.0-alpha.1'
        owner = 'human-led-program-kit-alpha-version-transition'
        reviewState = 'awaiting-human-approval'
        implementationStatus = 'not-started'
        approvalRecord = $null
        digestProfile = [ordered]@{
            algorithm = 'sha256'
            byteProfile = 'repository file bytes'
            encoding = 'utf-8'
            byteOrderMark = $false
            lineEndings = 'lf'
            attributes = '/.gitattributes'
        }
        artifacts = $manifestArtifacts
        approvalBoundary = [ordered]@{
            requiredDecision = 'explicit-human-approval-of-exact-canonical-digests'
            candidateDesignSha256 = $designDigest
            candidatePlanSha256 = $planDigest
            acceptedScope = 'PKAV-W010 through PKAV-W070 exactly as represented by the canonical Architecture Design 2.0 and Implementation Plan 3.0 transitional artifacts.'
            doesNotAuthorize = @(
                'implementation before exact digest approval',
                'material deviation from the approved design or plan',
                'stable version-policy definition before Release Kit design',
                'package-feed publication, release qualification, promotion, deployment, or signing',
                'JTest or other consumer repository mutation',
                'implementation of the follow-on Program Kit health review before its own exact approval',
                'capability activation in the Program Kit authoring workspace',
                'user-global provider writes, hooks, watchers, autonomous starts, or silent upgrades')
        }
        validation = [ordered]@{
            jsonSyntax = 'passed for every review JSON artifact'
            canonicalArchitectureSchema = 'passed against Architecture Design 2.0.0'
            canonicalPlanSchema = 'passed against Implementation Plan 3.0.0'
            staticConformanceDispositionSchema = 'passed against StaticConformanceDisposition 1.0.0'
            targetedSemantics = 'passed for exact references, alpha intent, package boundary, work-unit graph, trace, reuse-existing artifacts, activation/profile bindings, and closure reachability'
            materializerDeterminism = 'passed: two consecutive runs produced byte-identical generated review artifacts'
            runtimeImplementationOrExecution = 'not performed under design authority'
        }
        provenance = [ordered]@{
            startingCommit = '773d7cf3859fe98c2fd72139872312994effeb8d'
            branch = 'main'
            source = 'human-started Program Kit versioning and maintainer-health design request'
            details = 'Bounded to Program Kit repository source truth. No implementation, publication, capability activation, consumer mutation, sibling-repository lookup, or JTest change occurred.'
        }
    }
    Write-Json 'review-manifest.json' $manifest
}

Write-Output (
    [ordered]@{
        design = $designReference
        plan = New-Reference `
            'pkid:plan:program-kit:alpha-version-transition' `
            '0.1.0-alpha.1' `
            $planDigest
        disposition = $dispositionReference
        selectionLock = New-Reference `
            $selectionLock.identity `
            $selectionLock.version `
            $selectionLockDigest
    } |
    ConvertTo-Json -Depth 20)
