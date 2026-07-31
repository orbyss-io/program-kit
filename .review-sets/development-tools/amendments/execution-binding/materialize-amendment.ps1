[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$amendmentRoot = $PSScriptRoot
$reviewSetRoot = [IO.Path]::GetFullPath((Join-Path $amendmentRoot '..\..'))
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $reviewSetRoot '..\..'))
$utf8 = [Text.UTF8Encoding]::new($false, $true)
$baseCommit = '01a9a820d422d92da7f2df977db66c4d4f888924'
$baseDesignDigest = 'a44f13b3a34fb01b6c336ba2069cef9278f3f4bc27d9e128f5df05cf30c66592'
$basePlanDigest = '0ee9304510bbfaa6de508bf4fd5f0726625cb33e77aced26cbfe5a15db72c5a3'
$baseDispositionDigest = 'e956991542cd36a5869f6e214fb8168250d3739383f33b1c80b103fe00062e81'
$baseApprovalDigest = '8b8eec00e88e94a0fb544973ff7b7f1d95a9eff6aacd462b45e28e73d6111ceb'
$matrixDigest = '9603f5e67d256b381df4e69dce99fd9aafeaded20c947cfe699adb9dec7ecd8b'
$baselineProfileDigest = '80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d'
$currentProfileDigest = '2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f'
$acceptedProfileVersions = '[1.0.0,1.1.0)'

function Assert-True([bool] $condition, [string] $message) {
    if (-not $condition) {
        throw $message
    }
}

function Get-LfDigest([string] $path) {
    $bytes = [IO.File]::ReadAllBytes($path)
    Assert-True `
        (-not ($bytes.Length -ge 3 -and
            $bytes[0] -eq 0xef -and
            $bytes[1] -eq 0xbb -and
            $bytes[2] -eq 0xbf)) `
        "UTF-8 byte-order mark is not allowed: $path"
    $text = $utf8.GetString($bytes)
    $normalized = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    $normalizedBytes = [Text.UTF8Encoding]::new($false).GetBytes($normalized)
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($normalizedBytes)
    ).ToLowerInvariant()
}

function Assert-Digest([string] $path, [string] $expected) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Missing source artifact: $path"
    $actual = Get-LfDigest $path
    Assert-True ($actual -eq $expected) "Source artifact digest differs: $path ($actual)"
}

function Write-Utf8Lf([string] $path, [string] $text) {
    $normalized = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    if (-not $normalized.EndsWith("`n", [StringComparison]::Ordinal)) {
        $normalized += "`n"
    }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null
    [IO.File]::WriteAllText(
        $path,
        $normalized,
        [Text.UTF8Encoding]::new($false))
}

function Write-Json([string] $name, [object] $value) {
    $path = Join-Path $amendmentRoot $name
    Write-Utf8Lf $path ($value | ConvertTo-Json -Depth 100)
}

function Read-Json([string] $path) {
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -Depth 100
}

function New-Reference(
    [string] $identity,
    [string] $version,
    [string] $digest
) {
    return [ordered]@{
        identity = $identity
        version = $version
        digest = "sha256:$digest"
    }
}

function Copy-ObjectWithReplacements(
    [object] $source,
    [Collections.IDictionary] $replacements
) {
    $result = [ordered]@{}
    foreach ($property in $source.PSObject.Properties) {
        if ($replacements.Contains($property.Name)) {
            $result[$property.Name] = $replacements[$property.Name]
        } else {
            $result[$property.Name] = $property.Value
        }
    }
    return $result
}

function New-ApprovalFixedBinding([object] $artifact) {
    return [ordered]@{
        resolutionMode = 'approval-fixed'
        approvedArtifact = $artifact
        approvedIdentity = $null
        acceptedVersions = $null
        compatibilityPolicy = $null
    }
}

function New-ExecutionResolvedBinding([object] $policyReference) {
    return [ordered]@{
        resolutionMode = 'execution-resolved'
        approvedArtifact = $null
        approvedIdentity = 'pkid:profile:program-kit:private-csharp-gate-exhaustive'
        acceptedVersions = $acceptedProfileVersions
        compatibilityPolicy = $policyReference
    }
}

function Append-Line([Text.StringBuilder] $builder, [string] $value = '') {
    [void] $builder.AppendLine($value)
}

function Get-CommandText([object] $verification) {
    $arguments = @($verification.arguments | ForEach-Object {
        if ($_ -match '[\s`"]') {
            '"' + $_.Replace('"', '\"') + '"'
        } else {
            $_
        }
    })
    return (@($verification.executable) + $arguments) -join ' '
}

$designPath = Join-Path $reviewSetRoot 'architecture-design.json'
$planPath = Join-Path $reviewSetRoot 'implementation-plan.json'
$dispositionPath = Join-Path $reviewSetRoot 'static-conformance-disposition.json'
$approvalPath = Join-Path $reviewSetRoot 'design-plan-approval.json'
$matrixPath = Join-Path $repositoryRoot 'Directory.Build.targets'
$profilePath = Join-Path $repositoryRoot 'build\Invoke-CSharpGateTestPlan.ps1'

Assert-Digest $designPath $baseDesignDigest
Assert-Digest $planPath $basePlanDigest
Assert-Digest $dispositionPath $baseDispositionDigest
Assert-Digest $approvalPath $baseApprovalDigest
Assert-Digest $matrixPath $matrixDigest
Assert-Digest $profilePath $currentProfileDigest

$approval = Read-Json $approvalPath
Assert-True ($approval.decision -eq 'approved') 'The frozen review set is not approved.'
Assert-True ($approval.supersession.state -eq 'active') 'The frozen approval is not active.'
Assert-True ($approval.design.digest -eq "sha256:$baseDesignDigest") 'The approval design differs.'
Assert-True ($approval.plan.digest -eq "sha256:$basePlanDigest") 'The approval plan differs.'

$baseDesign = Read-Json $designPath
$basePlan = Read-Json $planPath
$baseDisposition = Read-Json $dispositionPath

$staticBasis = [ordered]@{
    identity = 'pkid:design:program-kit:development-tools-execution-binding-static-basis'
    version = '0.1.0-alpha.3'
    sourceCommit = $baseCommit
    frozenApproval = New-Reference `
        'pkid:approval:program-kit:development-tools-review-set' `
        '3.0.0' `
        $baseApprovalDigest
    frozenDesign = New-Reference `
        'pkid:design:program-kit:development-tools' `
        '3.0.0' `
        $baseDesignDigest
    frozenDisposition = New-Reference `
        'pkid:static-conformance-disposition:program-kit:development-tools' `
        '2.0.0' `
        $baseDispositionDigest
    purpose = 'Provide a non-circular current design-flow basis for the already approved reuse-existing disposition while changing no Development Tools product invariant.'
    preservationRule = 'The current writer migration changes schema and artifact bindings only; the frozen design, disposition, requirements, work units, authority boundaries, and product semantics remain governing.'
}
Write-Json 'static-conformance-design-basis.json' $staticBasis
$staticBasisDigest = Get-LfDigest (Join-Path $amendmentRoot 'static-conformance-design-basis.json')

$currentDisposition = [ordered]@{
    '$schema' = 'https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.2/static-conformance-disposition.schema.json'
}
$dispositionReplacements = [ordered]@{
    softwareDesign = New-Reference `
        'pkid:design:program-kit:development-tools-execution-binding-static-basis' `
        '0.1.0-alpha.3' `
        $staticBasisDigest
}
foreach ($property in $baseDisposition.PSObject.Properties) {
    if ($dispositionReplacements.Contains($property.Name)) {
        $currentDisposition[$property.Name] = $dispositionReplacements[$property.Name]
    } else {
        $currentDisposition[$property.Name] = $property.Value
    }
}
Write-Json 'static-conformance-disposition.json' $currentDisposition
$currentDispositionDigest = Get-LfDigest (Join-Path $amendmentRoot 'static-conformance-disposition.json')

$currentDesign = [ordered]@{
    '$schema' = 'https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.3/architecture-design.schema.json'
}
$designReplacements = [ordered]@{
    staticConformanceDisposition = New-Reference `
        'pkid:static-conformance-disposition:program-kit:development-tools' `
        '0.1.0-alpha.2' `
        $currentDispositionDigest
}
foreach ($property in $baseDesign.PSObject.Properties) {
    if ($designReplacements.Contains($property.Name)) {
        $currentDesign[$property.Name] = $designReplacements[$property.Name]
    } else {
        $currentDesign[$property.Name] = $property.Value
    }
}
Write-Json 'architecture-design.json' $currentDesign
$currentDesignDigest = Get-LfDigest (Join-Path $amendmentRoot 'architecture-design.json')

$compatibilityPolicy = [ordered]@{
    identity = 'pkid:compatibility-policy:program-kit:development-tools-private-gate-verification-profile'
    version = '0.1.0-alpha.1'
    sourceCommit = $baseCommit
    approvedIdentity = 'pkid:profile:program-kit:private-csharp-gate-exhaustive'
    acceptedVersions = $acceptedProfileVersions
    approvedBaseline = New-Reference `
        'pkid:profile:program-kit:private-csharp-gate-exhaustive' `
        '1.0.0' `
        $baselineProfileDigest
    currentCompatibleSelection = New-Reference `
        'pkid:profile:program-kit:private-csharp-gate-exhaustive' `
        '1.0.1' `
        $currentProfileDigest
    compatibilityCriteria = @(
        'The selected artifact retains the exact private-csharp-gate-exhaustive identity.',
        'The selected version is inside the finite 1.0.x range and the exact selected digest is recorded in execution evidence.',
        'The profile continues to run the approved complete private Program Kit gate categories and refuses zero-test selection.',
        'Changes may adapt invocation mechanics, including explicit Microsoft.Testing.Platform selectors, without widening source scope, authority, required outcomes, allowed edits, stop conditions, package selection, or product semantics.'
    )
    materialDrift = @(
        'A different profile identity or a version outside the accepted range.',
        'Removal, weakening, or semantic reinterpretation of an approved verification category or failure condition.',
        'Any change to Development Tools scope, authority, required outcomes, allowed edits, stop conditions, package selection, product semantics, or the compatibility policy itself.'
    )
    receiptRequirements = @(
        'Record the approved binding, exact selected identity, version and digest, and this exact compatibility-policy artifact.',
        'Block before implementation when the selected artifact or compatibility evidence is missing, stale, outside range, or materially incompatible.'
    )
}
Write-Json 'verification-profile-compatibility-policy.json' $compatibilityPolicy
$compatibilityPolicyDigest = Get-LfDigest (
    Join-Path $amendmentRoot 'verification-profile-compatibility-policy.json')
$compatibilityPolicyReference = New-Reference `
    $compatibilityPolicy.identity `
    $compatibilityPolicy.version `
    $compatibilityPolicyDigest

$currentUnits = @()
foreach ($baseUnit in $basePlan.workUnits) {
    $unitReplacements = [ordered]@{
        activationMatrix = New-ApprovalFixedBinding $baseUnit.activationMatrix
        verificationProfile = New-ExecutionResolvedBinding $compatibilityPolicyReference
    }
    $currentUnits += Copy-ObjectWithReplacements $baseUnit $unitReplacements
}

$currentPlan = [ordered]@{
    '$schema' = 'https://schemas.orbyss.io/program-kit/planning/implementation-plan/0.1.0-alpha.5/schema.json'
}
$planReplacements = [ordered]@{
    design = New-Reference `
        'pkid:design:program-kit:development-tools' `
        '0.1.0-alpha.3' `
        $currentDesignDigest
    workUnits = $currentUnits
    staticConformanceDisposition = New-Reference `
        'pkid:static-conformance-disposition:program-kit:development-tools' `
        '0.1.0-alpha.2' `
        $currentDispositionDigest
}
foreach ($property in $basePlan.PSObject.Properties) {
    if ($planReplacements.Contains($property.Name)) {
        $currentPlan[$property.Name] = $planReplacements[$property.Name]
    } else {
        $currentPlan[$property.Name] = $property.Value
    }
}
Write-Json 'implementation-plan.json' $currentPlan
$currentPlanDigest = Get-LfDigest (Join-Path $amendmentRoot 'implementation-plan.json')

$projection = [Text.StringBuilder]::new()
Append-Line $projection '# Development Tools alpha.5 execution-binding implementation plan amendment'
Append-Line $projection
Append-Line $projection '> Non-authoritative human-readable projection. The canonical source is'
Append-Line $projection '> `implementation-plan.json`. If this projection and the canonical JSON differ,'
Append-Line $projection '> the canonical JSON governs. This document grants no implementation authority.'
Append-Line $projection
Append-Line $projection "Canonical SHA-256: ``sha256:$currentPlanDigest``."
Append-Line $projection "Source commit: ``$baseCommit``."
Append-Line $projection "Frozen approved plan SHA-256: ``sha256:$basePlanDigest``."
Append-Line $projection 'State: `ready-for-human-decision`; implementation remains `not-started`.'
Append-Line $projection 'Static conformance remains the approved `reuse-existing` decision.'
Append-Line $projection
Append-Line $projection '## Exact amendment'
Append-Line $projection
Append-Line $projection '- Every requirement, dependency, required outcome, input, output, allowed edit, compatibility obligation, stop condition, verification command, trace, gate selection, selection lock, and activation-evidence reference is preserved from the approved plan.'
Append-Line $projection '- Every activation matrix is `approval-fixed` to `pkid:activation-matrix:program-kit:private-csharp-gate-build-spine@1.0.0`, digest `sha256:9603f5e67d256b381df4e69dce99fd9aafeaded20c947cfe699adb9dec7ecd8b`.'
Append-Line $projection '- Every verification profile is `execution-resolved` for `pkid:profile:program-kit:private-csharp-gate-exhaustive` within `[1.0.0,1.1.0)` under the exact compatibility policy.'
Append-Line $projection '- The current compatible selection is `1.0.1`, digest `sha256:2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f`; execution must record an exact binding receipt.'
Append-Line $projection '- Scope, authority, product semantics, package selection, required outcomes, allowed edits, and stop conditions cannot be execution-resolved.'
Append-Line $projection
Append-Line $projection '## Work units'
foreach ($unit in $currentPlan.workUnits) {
    Append-Line $projection
    Append-Line $projection "### $($unit.workUnitId)"
    Append-Line $projection
    $dependencies = if (@($unit.dependsOn).Count -eq 0) { 'none' } else { @($unit.dependsOn) -join ', ' }
    Append-Line $projection "**Depends on:** $dependencies"
    Append-Line $projection
    Append-Line $projection '**Required outcome**'
    Append-Line $projection
    Append-Line $projection $unit.requiredOutcome
    Append-Line $projection
    Append-Line $projection '**Allowed edits**'
    Append-Line $projection
    foreach ($allowedEdit in $unit.allowedEdits) {
        Append-Line $projection "- $allowedEdit"
    }
    Append-Line $projection
    Append-Line $projection '**Verification**'
    Append-Line $projection
    foreach ($verification in $unit.verification) {
        Append-Line $projection "- ``$(Get-CommandText $verification)`` from ``$($verification.workingDirectory)``."
        Append-Line $projection "  Expected: $($verification.expectedObservation)"
    }
    Append-Line $projection
    Append-Line $projection '**Stop conditions**'
    Append-Line $projection
    foreach ($condition in $unit.stopConditions) {
        Append-Line $projection "- $condition"
    }
}
Append-Line $projection
Append-Line $projection '## Requirement trace'
Append-Line $projection
foreach ($trace in $currentPlan.trace) {
    Append-Line $projection "- ``$($trace.requirementId)``: $(@($trace.workUnitIds) -join ', '). $($trace.implementationOutcome)"
}
Append-Line $projection
Append-Line $projection '## Exact approval boundary'
Append-Line $projection
Append-Line $projection "Approval must identify architecture design ``sha256:$currentDesignDigest``, static-conformance disposition ``sha256:$currentDispositionDigest``, compatibility policy ``sha256:$compatibilityPolicyDigest``, and canonical plan ``sha256:$currentPlanDigest``."
Append-Line $projection 'Approval authorizes only execution of the preserved PKDT-W010 through PKDT-W110 plan with successful compatible binding resolution. It does not authorize provider trust or permission, user-global writes, application semantic approval, publication, release, deployment, external-repository mutation, or autonomous behavior.'
Append-Line $projection 'Any unresolved, incompatible, missing, stale, or materially changed selection stops before implementation and requires renewed human review.'
Write-Utf8Lf (Join-Path $amendmentRoot 'implementation-plan.md') $projection.ToString()
$projectionDigest = Get-LfDigest (Join-Path $amendmentRoot 'implementation-plan.md')

$manifest = [ordered]@{
    artifactId = 'pkid:plan-amendment:program-kit:development-tools-execution-binding'
    artifactVersion = '0.1.0-alpha.1'
    sourceCommit = $baseCommit
    state = 'ready-for-human-decision'
    frozenReviewSet = [ordered]@{
        identity = 'pkid:review-set:program-kit:development-tools'
        version = '3.0.0'
        designSha256 = "sha256:$baseDesignDigest"
        planSha256 = "sha256:$basePlanDigest"
        dispositionSha256 = "sha256:$baseDispositionDigest"
        approvalSha256 = "sha256:$baseApprovalDigest"
        approvalState = 'active'
    }
    preservation = [ordered]@{
        productSemantics = 'exact'
        workUnitGraph = 'exact'
        activationMatrix = 'approval-fixed'
        verificationProfile = 'execution-resolved'
        acceptedVerificationProfileVersions = $acceptedProfileVersions
        implementationAuthority = 'not-granted'
    }
    artifacts = @(
        [ordered]@{ path = 'static-conformance-design-basis.json'; identity = $staticBasis.identity; version = $staticBasis.version; sha256 = "sha256:$staticBasisDigest" },
        [ordered]@{ path = 'static-conformance-disposition.json'; identity = 'pkid:static-conformance-disposition:program-kit:development-tools'; version = '0.1.0-alpha.2'; sha256 = "sha256:$currentDispositionDigest" },
        [ordered]@{ path = 'architecture-design.json'; identity = 'pkid:design:program-kit:development-tools'; version = '0.1.0-alpha.3'; sha256 = "sha256:$currentDesignDigest" },
        [ordered]@{ path = 'verification-profile-compatibility-policy.json'; identity = $compatibilityPolicy.identity; version = $compatibilityPolicy.version; sha256 = "sha256:$compatibilityPolicyDigest" },
        [ordered]@{ path = 'implementation-plan.json'; identity = 'pkid:plan:program-kit:development-tools-execution-binding'; version = '0.1.0-alpha.5'; sha256 = "sha256:$currentPlanDigest" },
        [ordered]@{ path = 'implementation-plan.md'; identity = 'pkid:projection:program-kit:development-tools-execution-binding-plan'; version = '0.1.0-alpha.1'; sha256 = "sha256:$projectionDigest" }
    )
    approvalBoundary = [ordered]@{
        decision = 'awaiting-exact-human-approval'
        requiredArtifactDigests = @(
            "sha256:$currentDesignDigest",
            "sha256:$currentDispositionDigest",
            "sha256:$compatibilityPolicyDigest",
            "sha256:$currentPlanDigest"
        )
        implementationMayStart = $false
        materialDeviationRequiresRenewedApproval = $true
    }
}
Write-Json 'review-manifest.json' $manifest
$manifestDigest = Get-LfDigest (Join-Path $amendmentRoot 'review-manifest.json')

$readme = @'
# Development Tools alpha.5 execution-binding amendment

This review amendment is materialized against Program Kit commit
`{{baseCommit}}`. It preserves the active human approval of the exact Development
Tools `3.0.0` design and plan while repairing only the stale exhaustive-profile
binding through Planning `0.1.0-alpha.5`.

The approved activation matrix remains exact and `approval-fixed`. The
verification profile becomes `execution-resolved` for the same approved
identity within the finite `1.0.x` line under one exact compatibility policy.
The selected identity, version, digest, and policy must be recorded as trusted
execution evidence before any work unit starts.

No Development Tools requirement, work-unit dependency, required outcome,
allowed edit, stop condition, package selection, authority boundary, product
semantic, static-conformance decision, gate definition, selection lock, or
activation evidence is changed. The frozen review set and its active approval
remain byte-identical.

## Review order

1. `static-conformance-design-basis.json` — non-circular binding to the frozen
   approved design and disposition.
2. `static-conformance-disposition.json` — current-writer projection of the
   approved `reuse-existing` decision.
3. `architecture-design.json` — current-writer projection with no semantic
   change.
4. `verification-profile-compatibility-policy.json` — the narrow execution
   resolution policy.
5. `implementation-plan.md` — readable non-authoritative review surface.
6. `implementation-plan.json` — canonical alpha.5 approval artifact.
7. `review-manifest.json` — exact source, preservation, digests, and approval
   boundary.

## Canonical digests

- Architecture Design: `sha256:{{currentDesignDigest}}`
- Static-conformance disposition: `sha256:{{currentDispositionDigest}}`
- Verification-profile compatibility policy: `sha256:{{compatibilityPolicyDigest}}`
- Implementation Plan: `sha256:{{currentPlanDigest}}`
- Human-readable plan projection: `sha256:{{projectionDigest}}`
- Review manifest: `sha256:{{manifestDigest}}`

## Authority

State is `ready-for-human-decision`. These artifacts grant no implementation,
provider, trust, permission, publication, release, deployment, or external
mutation authority. Implementation may begin only after the human approves the
four exact canonical digests named by `review-manifest.json`.
'@
$readme = $readme.Replace('{{baseCommit}}', $baseCommit).Replace('{{currentDesignDigest}}', $currentDesignDigest).Replace('{{currentDispositionDigest}}', $currentDispositionDigest).Replace('{{compatibilityPolicyDigest}}', $compatibilityPolicyDigest).Replace('{{currentPlanDigest}}', $currentPlanDigest).Replace('{{projectionDigest}}', $projectionDigest).Replace('{{manifestDigest}}', $manifestDigest)
Write-Utf8Lf (Join-Path $amendmentRoot 'README.md') $readme

Write-Output "materialized Development Tools alpha.5 plan sha256:$currentPlanDigest"
