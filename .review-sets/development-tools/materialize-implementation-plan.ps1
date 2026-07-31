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
    '2.0.0' `
    $designDigest
$providerEvidenceReference = New-Reference `
    'pkid:evidence:program-kit:development-tools-provider-contract' `
    '2.0.0' `
    $providerEvidenceDigest
$dispositionReference = New-Reference `
    'pkid:static-conformance-disposition:program-kit:development-tools' `
    '1.0.0' `
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
        'Establish exact Development Tool 1.0.0 contracts and schemas in Orbyss.ProgramKit.Development, package/component version topology, canonical serialization and compatibility rules, and the approved reuse-existing static-gate binding.' `
        'schemas/development-tools; src/Orbyss.ProgramKit.Development; exact component/version maps; schema registration; focused fixtures, tests, documentation, solution, and lock files.' `
        'Schemas validate and canonicalize deterministically; compatibility/version topology and the unchanged private ProgramKit gate binding pass with zero gate, build, or test failures.' `
        'Stop if current accepted/implemented Console source materially conflicts with host-profile-neutral projection, a contract requires consumer semantics, topology cannot represent affected components, or implementation would create/extend a static gate.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W020' 20 @('PKDT-W010') `
        'Implement complete Open Console mapping/reporting, default-all exact-revision selection, fail-closed access policy, structured schema/token/result projection, and the minimal package-only generated Console challenge fixture.' `
        'Bounded Open Console Development Tool projection; declaration/mapping/manifest validation; isolated acceptance fixture and package preparation; controlled NuGet.Config/source mapping; focused tests, docs, solution, and lock files.' `
        'Complete mapping, selection, blocked diagnostics, structured projection, denied defaults, exact side effects, deterministic fixture output, repeated package-only construction, and every forbidden consumer-coupling test pass.' `
        'Stop if any operation is silently omitted or weakened, side effects/access are inferred, output is non-canonical/non-JSON, blocked selection cannot be represented, or the consumer uses ProgramKit project/source/build-output coupling.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W030' 30 @('PKDT-W020') `
        'Add Orbyss.ProgramKit.DevelopmentTools.Mcp and program-kit-development-tools-mcp as the single provider-neutral MCP 2025-11-25 stdio bridge with exact discovery, call/result, byte, process, timeout, cancellation, concurrency, idempotency, and failure behavior.' `
        'src/Orbyss.ProgramKit.DevelopmentTools.Mcp; exact MCP dependency/version topology; neutral bridge fixtures, process harnesses, tests, canonical docs, solution, and lock files.' `
        'Direct executable and raw MCP initialize/list/call, structured result, byte tamper, schema, timeout, cancellation race, concurrency, idempotency, stderr/stdout, process freshness, and non-autonomy conformance pass.' `
        'Stop on material MCP drift, stdout contamination, provider-specific runtime code, missing byte verification, unbounded behavior, automatic retry, implicit idempotency, shared consumers, provider/capability calls, or nested loops.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @((New-ProviderDependency `
            'Recheck exact MCP 2025-11-25 tools, stdio, and cancellation sources.'))),
    (New-WorkUnit `
        'PKDT-W040' 40 @('PKDT-W030') `
        'Implement deterministic registration proposal, exact digest acceptance, provider-specific ownership locks, atomic project mutation, read-only status, explicit update diff, exact removal, collision handling, and fail-closed drift detection in program-kit.' `
        'src/Orbyss.ProgramKit.CommandLine Development Tools grammar/transport; src/Orbyss.ProgramKit.Development registration core; normalized provider-entry adapters; registration fixtures, tests, docs, solution, and lock files.' `
        'Proposal determinism, digest refusal, status classifications, atomic register/update/remove, operation diff, ownership lock, path safety, unrelated-byte preservation, crash recovery, and no-process-start tests pass.' `
        'Stop if mutation can precede exact proposal acceptance, ownership/collision is ambiguous, status mutates, writes are non-atomic/uncontained, removal adopts/deletes unrelated state, or any command starts a process/provider/tool.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @()),
    (New-WorkUnit `
        'PKDT-W050' 50 @('PKDT-W040') `
        'Implement the Codex project writer and prove genuine Codex sessions A, B, and C discover, invoke, update, remove, and cease discovering the exact tool solely through persisted project registration.' `
        'Codex provider-entry writer in bounded registration code; .codex/config.toml fixtures; isolated acceptance workspaces; Codex evidence schemas/records/validators; tests and canonical docs.' `
        'Codex fixtures and genuine isolated A registration, cold B semantic-only discovery/invocation, update/negatives, exact removal, and cold C non-discovery evidence validate.' `
        'Stop on material Codex drift, unisolated sessions, inherited executable/path/command knowledge, user/global/trust/permission mutation, process survival, non-genuine discovery, or incomplete evidence.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @((New-ProviderDependency `
            'Recheck official Codex MCP/config sources and bind genuine isolated Codex A/B/C acceptance.'))),
    (New-WorkUnit `
        'PKDT-W060' 60 @('PKDT-W050') `
        'Implement the Claude Code project writer, locally prove exact .mcp.json proposal/register/status/update/remove behavior and provider-independent negatives, and package a deterministic external A/B/C acceptance kit.' `
        'Claude Code provider-entry writer in bounded registration code; .mcp.json fixtures; external acceptance-kit manifest/instructions/validators; Claude evidence schemas; tests and canonical docs.' `
        'Claude .mcp.json lifecycle fixtures, collision/tamper/permission-boundary negatives, unrelated-byte preservation, kit determinism, and returned-evidence validator tests pass without claiming genuine runtime acceptance.' `
        'Stop on material Claude Code drift, any need to write settings/trust/approval/permission state, user/global writes, hidden machine assumptions, non-deterministic kit bytes, or inability to validate returned evidence without local Claude.' `
        'product' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @((New-ProviderDependency `
            'Recheck official Claude Code MCP, permissions, and settings sources.'))),
    (New-WorkUnit `
        'PKDT-W070' 70 @('PKDT-W060') `
        'Validate genuine returned Claude Code A/B/C evidence, close the exact cross-provider acceptance matrix, complete canonical package/CLI/schema documentation, and record final evidence without overstating cross-model behavior.' `
        'Returned Claude Code evidence under the exact schema; cross-provider closure records; package/CLI/schema canonical documentation; acceptance fixtures/goldens; review validation and implementation evidence.' `
        'Locked restore, private gate, build, full unit/conformance suites, package-only proof, deterministic result, genuine Codex/Claude A/B/C evidence, complete negatives, closure, documentation ownership, and changed-file scope pass.' `
        'Stop and leave closure open if Claude evidence is missing, changed, fabricated, non-cold, incomplete, secret-bearing, or from different bytes; also stop on any suite, package-only, gate, documentation-authority, or scope failure.' `
        'closure' `
        $designReference `
        $activationMatrixReference `
        $verificationProfileReference `
        @())
)

$requirements = [ordered]@{
    'PKDT-R001' = 'Exact Development Tool, schema, package, executable, and MCP identities are versioned and digest-bound.'
    'PKDT-R002' = 'Every Open Console operation is selected, exactly excluded, or selected-but-blocked; none is silently omitted.'
    'PKDT-R003' = 'Structured projection invokes one fresh consumer process and validates one canonical JSON result.'
    'PKDT-R004' = 'Side effects, resources, timeout, cancellation, concurrency, retry, and idempotency are fail-closed.'
    'PKDT-R005' = 'The proof consumer uses only exact locally prepared packages and controlled NuGet source mapping.'
    'PKDT-R006' = 'Both providers use the same exact neutral MCP bridge.'
    'PKDT-R007' = 'Proposal/register/status/update/remove preserve exact ownership and human authority.'
    'PKDT-R008' = 'Codex owns only one reviewed project MCP entry.'
    'PKDT-R009' = 'Claude Code owns only one reviewed project MCP entry and no settings/trust/permission state.'
    'PKDT-R010' = 'Missing, tampered, incompatible, colliding, changed, or unowned bytes fail closed.'
    'PKDT-R011' = 'Both providers prove isolated A/B/C cold-session behavior.'
    'PKDT-R012' = 'The complete negative matrix has deterministic or genuine provider evidence.'
    'PKDT-R013' = 'Shared neutral digests match; provider observations remain labelled; closure waits for genuine Claude evidence.'
    'PKDT-R014' = 'No autonomous behavior exists and canonical documentation remains in ProgramKit.'
    'PKDT-R015' = 'Every change requires explicit reviewed update or migration/removal and fresh registration.'
    'PKDT-R016' = 'ProgramKit C# reuses the exact private gate and affected units recheck current Console source truth.'
}

$traceMap = [ordered]@{
    'PKDT-R001' = @('PKDT-W010','PKDT-W070')
    'PKDT-R002' = @('PKDT-W010','PKDT-W020','PKDT-W070')
    'PKDT-R003' = @('PKDT-W020','PKDT-W030','PKDT-W070')
    'PKDT-R004' = @('PKDT-W010','PKDT-W020','PKDT-W030','PKDT-W070')
    'PKDT-R005' = @('PKDT-W020','PKDT-W070')
    'PKDT-R006' = @('PKDT-W030','PKDT-W070')
    'PKDT-R007' = @('PKDT-W040','PKDT-W050','PKDT-W060','PKDT-W070')
    'PKDT-R008' = @('PKDT-W040','PKDT-W050','PKDT-W070')
    'PKDT-R009' = @('PKDT-W040','PKDT-W060','PKDT-W070')
    'PKDT-R010' = @('PKDT-W030','PKDT-W040','PKDT-W050','PKDT-W060','PKDT-W070')
    'PKDT-R011' = @('PKDT-W050','PKDT-W060','PKDT-W070')
    'PKDT-R012' = @('PKDT-W020','PKDT-W030','PKDT-W040','PKDT-W050','PKDT-W060','PKDT-W070')
    'PKDT-R013' = @('PKDT-W050','PKDT-W060','PKDT-W070')
    'PKDT-R014' = @('PKDT-W030','PKDT-W040','PKDT-W050','PKDT-W060','PKDT-W070')
    'PKDT-R015' = @('PKDT-W010','PKDT-W040','PKDT-W050','PKDT-W060','PKDT-W070')
    'PKDT-R016' = @('PKDT-W010','PKDT-W020','PKDT-W070')
}

$trace = @(
    foreach ($entry in $requirements.GetEnumerator()) {
        [ordered]@{
            requirementId = $entry.Key
            ownerId = 'pkid:domain:program-kit:development-tools'
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
    ownerId = 'pkid:domain:program-kit:development-tools'
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
        version = '1.0.0'
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

Write-Json 'implementation-plan.json' $plan
Write-Output (
    New-Reference `
        'pkid:plan:program-kit:development-tools' `
        '2.0.0' `
        (Get-Digest 'extensions/development-tools/implementation-plan.json') |
        ConvertTo-Json)
