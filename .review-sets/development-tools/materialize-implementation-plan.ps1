param(
    [string] $ExtensionRoot = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $ExtensionRoot '..\..')).Path

function Get-Digest([string] $relativePath) {
    return (
        Get-FileHash `
            -Algorithm SHA256 `
            -LiteralPath (Join-Path $repositoryRoot $relativePath)
    ).Hash.ToLowerInvariant()
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

function New-WorkUnit(
    [string] $id,
    [int] $sequence,
    [string[]] $dependsOn,
    [string] $outcome,
    [string] $allowedEdits,
    [string] $observation,
    [string] $stopCondition,
    [string] $kind,
    [object] $designReference,
    [object] $activationMatrix,
    [object] $verificationProfile,
    [object[]] $externalDependencies
) {
    return [ordered]@{
        workUnitId = $id
        requiredOutcome = $outcome
        sequence = $sequence
        parallelGroupId = $null
        dependsOn = $dependsOn
        inputs = @($designReference)
        outputs = @(
            [ordered]@{
                identity = 'pkid:plan-output:program-kit:' + $id.ToLowerInvariant()
                version = '1.0.0'
                state = 'prospective'
                integrityDigest = $null
            }
        )
        allowedEdits = @($allowedEdits)
        sourceDependencies = @()
        externalDependencies = $externalDependencies
        migrations = @()
        compatibility = @()
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
                expectedObservation = $observation
            }
        )
        selectedTests = @()
        workUnitKind = $kind
        activationMatrix = $activationMatrix
        verificationProfile = $verificationProfile
    }
}

function Write-Json([string] $name, [object] $value) {
    $json = $value | ConvertTo-Json -Depth 100
    $json = $json.Replace("`r`n", "`n") + "`n"
    [IO.File]::WriteAllText(
        (Join-Path $ExtensionRoot $name),
        $json,
        [Text.UTF8Encoding]::new($false))
}

function Write-Text([string] $name, [string] $value) {
    $text = $value.Replace("`r`n", "`n")
    [IO.File]::WriteAllText(
        (Join-Path $ExtensionRoot $name),
        $text,
        [Text.UTF8Encoding]::new($false))
}

function New-HumanPlanProjection(
    [object] $plan,
    [object] $requirements,
    [string] $planDigest
) {
    $builder = [Text.StringBuilder]::new()
    [void] $builder.AppendLine(
        '# Program Kit operation exposure and application capabilities — implementation plan')
    [void] $builder.AppendLine()
    [void] $builder.AppendLine(
        '> Non-authoritative human-readable projection. The canonical source is')
    [void] $builder.AppendLine(
        '> `implementation-plan.json`. If this projection and the canonical JSON differ,')
    [void] $builder.AppendLine(
        '> the canonical JSON governs. This document grants no implementation authority.')
    [void] $builder.AppendLine()
    [void] $builder.AppendLine(
        "Canonical SHA-256: ``sha256:$planDigest``")
    [void] $builder.AppendLine(
        'State: `ready-for-human-decision`; implementation remains `not-started`.')
    [void] $builder.AppendLine(
        'Static conformance: `reuse-existing`.')
    [void] $builder.AppendLine()
    [void] $builder.AppendLine('## Dependency order')
    [void] $builder.AppendLine()
    foreach ($workUnit in $plan.workUnits) {
        $dependencies = if ($workUnit.dependsOn.Count -eq 0) {
            'none'
        } else {
            $workUnit.dependsOn -join ', '
        }
        [void] $builder.AppendLine(
            "- ``$($workUnit.workUnitId)`` depends on: $dependencies")
    }

    [void] $builder.AppendLine()
    [void] $builder.AppendLine('## Work units')
    foreach ($workUnit in $plan.workUnits) {
        $dependencies = if ($workUnit.dependsOn.Count -eq 0) {
            'none'
        } else {
            $workUnit.dependsOn -join ', '
        }
        [void] $builder.AppendLine()
        [void] $builder.AppendLine(
            "### $($workUnit.workUnitId)")
        [void] $builder.AppendLine()
        [void] $builder.AppendLine(
            "**Depends on:** $dependencies")
        [void] $builder.AppendLine()
        [void] $builder.AppendLine('**Required outcome**')
        [void] $builder.AppendLine()
        [void] $builder.AppendLine($workUnit.requiredOutcome)
        [void] $builder.AppendLine()
        [void] $builder.AppendLine('**Allowed edits**')
        [void] $builder.AppendLine()
        foreach ($allowedEdit in $workUnit.allowedEdits) {
            [void] $builder.AppendLine("- $allowedEdit")
        }
        [void] $builder.AppendLine()
        [void] $builder.AppendLine('**Expected verification**')
        [void] $builder.AppendLine()
        foreach ($verification in $workUnit.verification) {
            [void] $builder.AppendLine(
                "- $($verification.expectedObservation)")
        }
        [void] $builder.AppendLine()
        [void] $builder.AppendLine('**Stop conditions**')
        [void] $builder.AppendLine()
        foreach ($stopCondition in $workUnit.stopConditions) {
            [void] $builder.AppendLine("- $stopCondition")
        }
    }

    [void] $builder.AppendLine()
    [void] $builder.AppendLine('## Requirements')
    [void] $builder.AppendLine()
    foreach ($entry in $requirements.GetEnumerator()) {
        $trace = $plan.trace |
            Where-Object { $_.requirementId -eq $entry.Key } |
            Select-Object -First 1
        [void] $builder.AppendLine(
            "- **$($entry.Key):** $($entry.Value) Work units: $($trace.workUnitIds -join ', ').")
    }

    [void] $builder.AppendLine()
    [void] $builder.AppendLine('## Approval boundary')
    [void] $builder.AppendLine()
    [void] $builder.AppendLine(
        'Approval must identify the exact canonical design and plan digests.')
    [void] $builder.AppendLine(
        'Approval would not authorize provider trust or permission, user-global writes,')
    [void] $builder.AppendLine(
        'application semantic approval, publication, release, deployment, external')
    [void] $builder.AppendLine(
        'repository mutation, or autonomous behavior. Material deviation stops for')
    [void] $builder.AppendLine('renewed human design review.')
    [void] $builder.AppendLine()
    [void] $builder.AppendLine(
        '_Generated deterministically beside the canonical plan by_')
    [void] $builder.AppendLine(
        '_`materialize-implementation-plan.ps1`._')

    return $builder.ToString().Replace("`r`n", "`n")
}

$designDigest = Get-Digest `
    'extensions/development-tools/architecture-design.json'
$providerEvidenceDigest = Get-Digest `
    'extensions/development-tools/provider-contract-evidence.json'
$dispositionDigest = Get-Digest `
    'extensions/development-tools/static-conformance-disposition.json'
$selectionLockDigest = Get-Digest `
    'extensions/development-tools/program-kit-private-gate-selection-lock.json'
$gateDesignDigest = Get-Digest `
    'extensions/reusable-csharp-build-gates/architecture-design.json'
$gateDefinitionDigest = Get-Digest `
    'governance/csharp-source-quality-gate.md'
$activationMatrixDigest = Get-Digest 'Directory.Build.targets'
$verificationProfileDigest = Get-Digest `
    'build/Invoke-CSharpGateTestPlan.ps1'
$activationEvidenceDigest = Get-Digest `
    'extensions/reusable-csharp-build-gates/implementation-evidence/closure.json'

$designReference = New-Reference `
    'pkid:design:program-kit:development-tools' `
    '3.0.0' `
    $designDigest
$providerEvidenceReference = New-Reference `
    'pkid:evidence:program-kit:development-tools-provider-contract' `
    '3.0.0' `
    $providerEvidenceDigest
$dispositionReference = New-Reference `
    'pkid:static-conformance-disposition:program-kit:development-tools' `
    '2.0.0' `
    $dispositionDigest
$activationMatrixReference = New-Reference `
    'pkid:activation-matrix:program-kit:private-csharp-gate-build-spine' `
    '1.0.0' `
    $activationMatrixDigest
$verificationProfileReference = New-Reference `
    'pkid:profile:program-kit:private-csharp-gate-exhaustive' `
    '1.0.0' `
    $verificationProfileDigest

function New-ProviderDependency([string] $purpose) {
    return [ordered]@{
        artifact = $providerEvidenceReference
        purpose = $purpose
    }
}

$workUnits = @(
    (New-WorkUnit `
        'PKDT-W010' 10 @() `
        'Generalize the implemented operation contracts into one host-neutral OperationContractCatalog plus explicit exposure bindings, preserving exact operation identity/revision and the approved reuse-existing Program Kit static-gate binding.' `
        'schemas/operations and bounded operation-contract source, registry, serialization, compatibility, fixtures, tests, documentation, solution, package, and lock files. Do not edit or reinterpret the completed Program Kit health-patching extension.' `
        'Catalogs and bindings validate and canonicalize deterministically; one semantic operation revision can bind Console and OpenAPI exposures without duplicating semantics; all current operation contracts remain compatible; current private gate, build, and tests pass.' `
        'Stop if current operation/Open Console source contradicts host-neutral identity, an exposure must become semantic authority, the health-patching task would be widened, or implementation would create or extend a static gate.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W020' 20 @('PKDT-W010') `
        'Project exact generated Console and generated API hosts from exposure bindings, including reserved host-owned structured Console introspection over the complete catalog or one selected operation with deterministic syntax and collision refusal.' `
        'Bounded generated Console/OpenAPI projection, host metadata, reserved introspection grammar, serializers, collision validation, fixtures, tests, documentation, solution, package, and lock files.' `
        'Help/completion remain human-facing; structured introspection exposes only catalog facts, composes no application service, invents no domain meaning, contains no secrets, selects exact aliases/paths, and refuses every reserved-token collision deterministically.' `
        'Stop if introspection requires a domain command, invokes application services, weakens host-neutral identity, exposes secrets, invents semantics, or Open Console/OpenAPI compatibility cannot be preserved.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W030' 30 @('PKDT-W020') `
        'Implement one provider-neutral stdio MCP bridge that mechanically projects the same operation catalog into exact tool names, descriptions, input/output schemas, results, failures, and direct operation invocation across the current modern and legacy MCP eras.' `
        'Bounded MCP bridge project/executable, discovery negotiation, tools list/call projection, process adapter, fixtures, tests, canonical documentation, solution, package, and lock files.' `
        'Modern server/discover and legacy initialize negotiate independently; tools/list is primary; direct one-operation MCP works without any capability; results remain application-owned; timeout, cancellation, concurrency, stdout/stderr, byte integrity, and failure behavior pass.' `
        'Stop on material MCP contract drift, provider-specific bridge code, stdout contamination, invented result semantics, shared mutable consumer execution, missing exact byte verification, automatic retry, nested model/tool loops, or capability-as-transport behavior.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @((New-ProviderDependency `
            'Recheck exact modern and legacy MCP discovery, tools, schemas, stdio, cancellation, and metadata contracts before implementation.'))),
    (New-WorkUnit `
        'PKDT-W040' 40 @('PKDT-W030') `
        'Implement deterministic project-scoped tool-registration proposal, exact human acceptance, provider ownership locks, status, update, and removal while keeping registration, trust/permission, and invocation as separate transitions.' `
        'Bounded Development Tools registration core and CLI grammar; Codex and Claude Code project MCP entry renderers; proposal/lock schemas; atomic mutation, collision, drift, fixtures, tests, docs, solution, package, and lock files.' `
        'Proposal bytes are deterministic; no provider/workspace mutation occurs before exact acceptance; status is read-only; update and removal preserve unrelated bytes; trust/permission remains provider-owned; no command starts a provider or tool.' `
        'Stop if mutation can precede acceptance, ownership is ambiguous, user/global provider state is required, status mutates, writes are uncontained/non-atomic, removal adopts unrelated state, or registration implies trust, permission, or invocation.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @(
            (New-ProviderDependency `
                'Recheck current Codex project MCP configuration and trust boundaries.'),
            (New-ProviderDependency `
                'Recheck current Claude Code project MCP configuration, trust, permission, and approval boundaries.'))),
    (New-WorkUnit `
        'PKDT-W050' 50 @('PKDT-W010') `
        'Define the optional application-authored outcome-capability bundle, deterministic descriptor/procedure/knowledge-closure structure, exact operation/schema bindings, composition/handoff rules, publisher attestation boundary, readiness checks, and authoring safeguard.' `
        'Generic capability bundle/descriptor/procedure/knowledge-closure schemas and verifier; compatibility, authoring diagnostics/materializers, fixtures, tests, documentation, solution, package, and lock files.' `
        'One or many operations may support a meaningful outcome; one-operation capabilities require real intake, interpretation, remediation, or safety value; required bindings and transitive closure preflight exactly; Program Kit validates conformance without authoring or approving domain semantics.' `
        'Stop if the contract creates one capability per command, universal workflow/result state, inferred domain semantics, prose-only closure, implicit authority, required source checkout, or a new capability/provider wrapper under implementation rather than an application-authored test fixture.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W060' 60 @('PKDT-W050') `
        'Generalize the existing capability bundle engine to acquire exact public local-directory, zip, NuGet, HTTPS, and GitHub-release sources, normalize carriers, verify publisher/package/tool/catalog/capability/adapter/closure identities and digests, and store immutable content by digest.' `
        'Bounded existing capability bundle verifier/acquisition/storage source and CLI source-kind parsing; carrier adapters; schemas, fixtures, tests, documentation, solution, package, and lock files.' `
        'Every source kind converges on one verified normalized bundle; format and location are explicit; mutable references resolve to locked immutable bytes; traversal, collision, ambiguity, partial acquisition, and digest mismatch fail closed; private/authenticated acquisition remains unsupported.' `
        'Stop if separate lifecycle engines emerge, a remote source activates content, credentials are required, runtime packages reference session capability content, carrier semantics leak into canonical bundles, or immutable bytes cannot be reproduced.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W070' 70 @('PKDT-W040','PKDT-W060') `
        'Implement the shared explicit capability lifecycle: deterministic initialize proposal, acceptance, provider/bundle ownership locks, refresh, update, status, removal, preflight, canonical reads, pruning, provider projections, and one atomic flat workspace catalog.' `
        'Bounded existing capabilities CLI engine and provider renderers; workspace content store, locks, flat catalog, discover-capabilities projection, transactional filesystem support, schemas, fixtures, tests, documentation, solution, package, and lock files.' `
        'Installation activates nothing; initialize and tool registration remain distinct accepted transitions; provider-native selection sees thin individual capabilities; discover-capabilities reads one flat grouped catalog; refresh repairs derived bytes only from unchanged locked sources; update alone accepts changed authoritative bytes; tampered locks fail closed.' `
        'Stop if refresh adopts new source or lock bytes, catalogs become authoritative/editable inputs, indexes nest, Program Kit adds confidence routing, provider trust/permission is mutated, initialization implies registration, or runtime/application executables edit AI workspace state.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @(
            (New-ProviderDependency `
                'Recheck current Codex project skill location, description activation, project trust, and MCP configuration.'),
            (New-ProviderDependency `
                'Recheck current Claude Code project skill location, model invocation, tool search, permissions, and MCP configuration.'))),
    (New-WorkUnit `
        'PKDT-W080' 80 @('PKDT-W070') `
        'Repackage Program Kit consumer capabilities as the reference generic application-capability payload with the same closure, digest, initialization, refresh, update, provider projection, catalog, and cold-session rules, preserving only a narrowly documented embedded-delivery bootstrap distinction.' `
        'Program Kit capability bundle payload/catalog/knowledge closure, package manifest, materializers, provider projections, package-only consumer fixtures, tests, documentation, solution, package, and lock files.' `
        'Every supported Program Kit consumer operation has package-only outcome guidance parity; cold sessions need no source checkout or internal memory; contributor architecture/debugging remains source-attached and separately initialized; the generic verifier treats Program Kit like any other publisher.' `
        'Stop if Program Kit dogfood receives semantic/conformance exceptions, consumer journeys require source/assembly/test-fixture archaeology, runtime references provider capability content, or contributor-only knowledge leaks into package-only consumer closure.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W090' 90 @('PKDT-W080') `
        'Close deterministic and package-only acceptance for host parity, direct MCP, capability closure and triggering fixtures, lifecycle authority, catalog drift/refresh/update, Program Kit dogfood, and every no-autonomy negative.' `
        'Isolated package-only applications/workspaces; JTest-shaped publisher fixture; Console/API/MCP fixtures; deterministic provider configuration fixtures; lifecycle/closure/tamper/collision tests; evidence schemas, records, docs, solution, package, and lock files.' `
        'All 42 reviewed fixtures pass, including cold semantic JTest-shaped outcome, direct MCP without capability, Console introspection parity, incomplete-closure refusal, changed-byte explicit update, refresh repair, no self-registration/permission/loop, and Program Kit package-only reference proof.' `
        'Stop if any fixture inherits syntax or source knowledge, application semantics are supplied by Program Kit, provider-native behavior is claimed from deterministic fixtures, changed bytes are silently accepted, or the active health-patching task is altered.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W100' 100 @('PKDT-W090') `
        'Prove genuine isolated Codex cold-session discovery, direct tool use, outcome-capability activation, guided registered-operation use, changed-byte refusal/update, refresh repair, removal, and non-discovery after removal from exact reviewed package bytes.' `
        'Isolated Codex acceptance workspaces; provider-labelled evidence schemas/records/validators; bounded acceptance scripts and canonical documentation. No user-global provider mutation.' `
        'Fresh Codex sessions use native tool and skill selection without inherited syntax, distinguish direct operation from outcome guidance, respect project trust/approval, reproduce exact evidence, and cease discovery after exact removal.' `
        'Stop on material Codex drift, non-cold or unisolated sessions, user/global writes, inherited command knowledge, fabricated/non-genuine selection, missing trust/approval observation, secret-bearing evidence, or different package/lock bytes.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @((New-ProviderDependency `
            'Bind genuine isolated Codex acceptance to the rechecked current official project MCP and skill contracts.'))),
    (New-WorkUnit `
        'PKDT-W110' 110 @('PKDT-W090','PKDT-W100') `
        'Validate genuine returned Claude Code evidence, close cross-provider and governance acceptance, finalize canonical documentation, and record completion without overstating Program Kit conformance as application semantic approval.' `
        'Exact returned Claude Code evidence; cross-provider closure records; publisher-attestation/conformance documentation; final acceptance records and validators; review validation and implementation evidence.' `
        'Locked restore, current private gate, build, full suites, package-only proofs, deterministic evidence, genuine provider-labelled Codex and Claude Code evidence, all negatives, documentation ownership, changed-file scope, and publisher/conformance distinction pass.' `
        'Stop and leave closure open if Claude evidence is unavailable, changed, fabricated, non-cold, incomplete, secret-bearing, or from different bytes; also stop on any suite, package-only, gate, no-autonomy, documentation-authority, or scope failure.' `
        'closure' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @((New-ProviderDependency `
            'Bind genuine returned Claude Code evidence to the rechecked current official project MCP, skill, and permission contracts.')))
)

$requirements = [ordered]@{
    'PKDT-R001' = 'One exact host-neutral operation identity/revision owns semantics across Console, OpenAPI, and MCP exposure bindings.'
    'PKDT-R002' = 'Generated Console structured introspection is reserved, host-owned, deterministic, collision-safe, non-executing, secret-free, and parity-complete.'
    'PKDT-R003' = 'The neutral MCP bridge supports current modern and legacy discovery/tool contracts and direct one-operation use without a capability.'
    'PKDT-R004' = 'Tool registration is deterministic and explicit; registration, provider trust/permission, and invocation remain separate.'
    'PKDT-R005' = 'Application capability bundles are optional, outcome-oriented, publisher-authored, and never mechanically one capability per command.'
    'PKDT-R006' = 'Capability procedures bind exact operation/schema identities and carry finite transitive knowledge closure, interpretation, remediation, authority, stop, and completion guidance.'
    'PKDT-R007' = 'Program Kit verifies integrity, compatibility, completeness, and package binding without authoring or approving application domain semantics.'
    'PKDT-R008' = 'Public local, NuGet, HTTPS, and GitHub-release carriers normalize through one verified acquisition and content-addressed storage engine.'
    'PKDT-R009' = 'Capability initialize, refresh, update, status, removal, preflight, reads, and pruning remain Program Kit CLI-owned and human-authorized.'
    'PKDT-R010' = 'Refresh repairs derived bytes only from unchanged trusted locks and bundles; update alone accepts changed authoritative bytes; lock tampering fails closed.'
    'PKDT-R011' = 'One derived flat workspace catalog supports on-demand discover-capabilities while provider-native selection owns normal activation.'
    'PKDT-R012' = 'Tool-ready and agent-guided readiness remain independent, exact, diagnostic, and non-authorizing.'
    'PKDT-R013' = 'Program Kit dogfoods the same generic application capability contract and proves every supported consumer operation from packages without source checkout.'
    'PKDT-R014' = 'Runtime packages and application executables remain isolated from provider-session content and never mutate AI workspace configuration or locks.'
    'PKDT-R015' = 'No universal result/workflow envelope, Program Kit confidence router, automatic registration/initialization, self-permission, retry, nested index, or autonomous model/tool loop exists.'
    'PKDT-R016' = 'Cold provider evidence proves semantic capability activation, direct MCP use, introspection parity, closure refusal, explicit changed-byte update, refresh repair, removal, and package-only Program Kit parity.'
    'PKDT-R017' = 'Official application content and publisher attestation remain distinct from Program Kit conformance and provider-labelled observations.'
    'PKDT-R018' = 'Program Kit-owned implementation reuses the exact current private gate and does not alter or widen the completed health-patching task.'
}

$traceMap = [ordered]@{
    'PKDT-R001' = @('PKDT-W010','PKDT-W020','PKDT-W030','PKDT-W090','PKDT-W110')
    'PKDT-R002' = @('PKDT-W020','PKDT-W090','PKDT-W110')
    'PKDT-R003' = @('PKDT-W030','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R004' = @('PKDT-W040','PKDT-W070','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R005' = @('PKDT-W050','PKDT-W080','PKDT-W090','PKDT-W110')
    'PKDT-R006' = @('PKDT-W050','PKDT-W060','PKDT-W070','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R007' = @('PKDT-W050','PKDT-W060','PKDT-W080','PKDT-W090','PKDT-W110')
    'PKDT-R008' = @('PKDT-W060','PKDT-W070','PKDT-W090','PKDT-W110')
    'PKDT-R009' = @('PKDT-W070','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R010' = @('PKDT-W070','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R011' = @('PKDT-W070','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R012' = @('PKDT-W050','PKDT-W070','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R013' = @('PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R014' = @('PKDT-W050','PKDT-W060','PKDT-W070','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R015' = @('PKDT-W030','PKDT-W040','PKDT-W050','PKDT-W070','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R016' = @('PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R017' = @('PKDT-W050','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
    'PKDT-R018' = @('PKDT-W010','PKDT-W020','PKDT-W030','PKDT-W040','PKDT-W050','PKDT-W060','PKDT-W070','PKDT-W080','PKDT-W090','PKDT-W100','PKDT-W110')
}

$trace = @(
    foreach ($entry in $requirements.GetEnumerator()) {
        [ordered]@{
            requirementId = $entry.Key
            ownerId = 'pkid:domain:program-kit:operation-exposure'
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
    ownerId = 'pkid:domain:program-kit:operation-exposure'
    state = 'ready-for-human-decision'
    requirementIds = @($requirements.Keys)
    workUnits = $workUnits
    parallelGroups = @()
    trace = $trace
    unresolvedDecisions = @()
    staticConformanceDisposition = $dispositionReference
    staticConformanceState = 'reuse-existing'
    gateDesign = New-Reference `
        'pkid:design:program-kit:reusable-csharp-build-gates' `
        '1.0.0' `
        $gateDesignDigest
    gateDefinition = [ordered]@{
        identity = 'pkid:policy:program-kit:csharp-source-quality-gate'
        version = '1.10.0'
        state = 'materialized'
        integrityDigest = 'sha256:' + $gateDefinitionDigest
    }
    selectionLock = [ordered]@{
        identity = 'pkid:selection-lock:program-kit:development-tools-private-gate'
        version = '2.0.0'
        state = 'materialized'
        integrityDigest = 'sha256:' + $selectionLockDigest
    }
    activationEvidence = [ordered]@{
        identity = 'pkid:evidence:program-kit:reusable-csharp-build-gates-closure'
        version = '1.0.0'
        state = 'materialized'
        integrityDigest = 'sha256:' + $activationEvidenceDigest
    }
}

$planPath = 'extensions/development-tools/implementation-plan.json'
Write-Json 'implementation-plan.json' $plan
$materializedPlanDigest = Get-Digest $planPath
Write-Text `
    'implementation-plan.md' `
    (New-HumanPlanProjection $plan $requirements $materializedPlanDigest)
Write-Output (
    New-Reference `
        'pkid:plan:program-kit:development-tools' `
        '3.0.0' `
        $materializedPlanDigest |
        ConvertTo-Json)
