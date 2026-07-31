param(
    [string] $ExtensionRoot = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $ExtensionRoot '..\..')).Path

function Assert-True([bool] $condition, [string] $message) {
    if (-not $condition) {
        throw $message
    }
}

function Get-Digest([string] $path) {
    return (
        Get-FileHash -Algorithm SHA256 -LiteralPath $path
    ).Hash.ToLowerInvariant()
}

function Get-RepositoryDigest([string] $relativePath) {
    return Get-Digest (Join-Path $repositoryRoot $relativePath)
}

function Read-Json([string] $name) {
    return Get-Content `
        -LiteralPath (Join-Path $ExtensionRoot $name) `
        -Raw |
        ConvertFrom-Json -Depth 100
}

function Assert-DigestReference(
    [object] $reference,
    [string] $relativePath,
    [string] $message
) {
    Assert-True `
        ($reference.digest -eq ('sha256:' + (Get-RepositoryDigest $relativePath))) `
        $message
}

$jsonFiles = Get-ChildItem -LiteralPath $ExtensionRoot -Filter '*.json'
foreach ($file in $jsonFiles) {
    $null = Get-Content -LiteralPath $file.FullName -Raw |
        ConvertFrom-Json -Depth 100
}

$basis = Read-Json 'static-conformance-design-basis.json'
$decision = Read-Json 'static-conformance-decision-source.json'
$disposition = Read-Json 'static-conformance-disposition.json'
$selection = Read-Json 'program-kit-private-gate-selection-lock.json'
$architecture = Read-Json 'architecture-design.json'
$plan = Read-Json 'implementation-plan.json'
$fixtures = Read-Json 'acceptance-fixtures.json'
$providerEvidence = Read-Json 'provider-contract-evidence.json'
$approvalAuthority = Read-Json 'approval-authority-source.json'
$approval = Read-Json 'design-plan-approval.json'
$manifest = Read-Json 'review-manifest.json'

Assert-DigestReference `
    $basis.intent `
    'extensions/development-tools/design-intent.md' `
    'The static basis does not bind the current design intent bytes.'
Assert-DigestReference `
    $basis.convergence `
    'extensions/development-tools/convergence-notes.md' `
    'The static basis does not bind the current convergence bytes.'
Assert-DigestReference `
    $decision.designBasis `
    'extensions/development-tools/static-conformance-design-basis.json' `
    'The human decision source does not bind the current static design basis.'
Assert-True `
    ($decision.decision.disposition -eq 'reuse-existing') `
    'The exact human static-conformance decision is not reuse-existing.'
Assert-True `
    ($disposition.disposition -eq 'reuse-existing') `
    'The static-conformance disposition is not reuse-existing.'
Assert-DigestReference `
    $disposition.softwareDesign `
    'extensions/development-tools/static-conformance-design-basis.json' `
    'The disposition does not bind the current non-circular design basis.'
Assert-DigestReference `
    $disposition.decisionSource.source `
    'extensions/development-tools/static-conformance-decision-source.json' `
    'The disposition does not bind the exact human decision source.'

$selectedGate = $disposition.gateSelections[0]
Assert-DigestReference `
    $selectedGate.gate `
    'governance/csharp-source-quality-gate.md' `
    'The selected gate does not bind the current private gate definition.'
Assert-DigestReference `
    $selectedGate.activationMatrix `
    'Directory.Build.targets' `
    'The selected gate does not bind the current Program Kit build spine.'
Assert-DigestReference `
    $selection.disposition `
    'extensions/development-tools/static-conformance-disposition.json' `
    'The gate selection lock does not bind the current disposition.'
Assert-DigestReference `
    $selection.gateDefinition `
    'governance/csharp-source-quality-gate.md' `
    'The gate selection lock does not bind the current gate definition.'
Assert-DigestReference `
    $selection.activationMatrix `
    'Directory.Build.targets' `
    'The gate selection lock does not bind the current activation matrix.'
Assert-DigestReference `
    $selection.verificationProfile `
    'build/Invoke-CSharpGateTestPlan.ps1' `
    'The gate selection lock does not bind the current verification profile.'
Assert-DigestReference `
    $selection.activationEvidence `
    'extensions/reusable-csharp-build-gates/implementation-evidence/closure.json' `
    'The gate selection lock does not bind the current reusable-gate closure evidence.'
Assert-True `
    ($selection.sourceCommit -eq $basis.sourceCommit) `
    'The gate selection lock and design basis do not share the same committed source basis.'

Assert-DigestReference `
    $architecture.staticConformanceDisposition `
    'extensions/development-tools/static-conformance-disposition.json' `
    'The architecture design does not bind the current static disposition.'
Assert-DigestReference `
    $plan.design `
    'extensions/development-tools/architecture-design.json' `
    'The implementation plan does not bind the current architecture design.'
Assert-DigestReference `
    $plan.staticConformanceDisposition `
    'extensions/development-tools/static-conformance-disposition.json' `
    'The implementation plan does not bind the current static disposition.'
Assert-True `
    ($plan.staticConformanceState -eq 'reuse-existing') `
    'The implementation plan does not carry reuse-existing.'
Assert-True `
    ($plan.selectionLock.integrityDigest -eq (
        'sha256:' + (
            Get-RepositoryDigest `
                'extensions/development-tools/program-kit-private-gate-selection-lock.json'
        )
    )) `
    'The implementation plan does not bind the current gate selection lock.'
Assert-True `
    ($plan.gateDefinition.integrityDigest -eq (
        'sha256:' + (Get-RepositoryDigest 'governance/csharp-source-quality-gate.md')
    )) `
    'The implementation plan does not bind the current gate definition.'
Assert-True `
    ($plan.activationEvidence.integrityDigest -eq (
        'sha256:' + (
            Get-RepositoryDigest `
                'extensions/reusable-csharp-build-gates/implementation-evidence/closure.json'
        )
    )) `
    'The implementation plan does not bind the current gate closure evidence.'

$workUnitIds = @($plan.workUnits | ForEach-Object { $_.workUnitId })
Assert-True `
    (($workUnitIds | Sort-Object -Unique).Count -eq $workUnitIds.Count) `
    'Implementation-plan work-unit IDs are not unique.'
foreach ($workUnit in $plan.workUnits) {
    foreach ($dependency in $workUnit.dependsOn) {
        Assert-True `
            ($workUnitIds -contains $dependency) `
            "Work unit $($workUnit.workUnitId) has unknown dependency $dependency."
        $dependencyUnit = $plan.workUnits |
            Where-Object { $_.workUnitId -eq $dependency } |
            Select-Object -First 1
        Assert-True `
            ($dependencyUnit.sequence -lt $workUnit.sequence) `
            "Work unit $($workUnit.workUnitId) has a non-preceding dependency."
    }
}

$requirementIds = @($plan.requirementIds)
Assert-True `
    (($requirementIds | Sort-Object -Unique).Count -eq $requirementIds.Count) `
    'Implementation-plan requirement IDs are not unique.'
$traceRequirementIds = @($plan.trace | ForEach-Object { $_.requirementId })
Assert-True `
    ($null -eq (Compare-Object $requirementIds $traceRequirementIds)) `
    'Implementation-plan trace does not cover every requirement exactly once.'
foreach ($trace in $plan.trace) {
    Assert-True `
        ($trace.workUnitIds.Count -gt 0) `
        "Requirement $($trace.requirementId) has no owning work unit."
    foreach ($workUnitId in $trace.workUnitIds) {
        Assert-True `
            ($workUnitIds -contains $workUnitId) `
            "Requirement $($trace.requirementId) references unknown work unit $workUnitId."
    }
}
Assert-True `
    ($plan.unresolvedDecisions.Count -eq 0) `
    'The implementation plan still contains an unresolved decision.'
Assert-True `
    ($architecture.unresolvedDecisions.Count -eq 0) `
    'The architecture design still contains an unresolved decision.'

$canonicalPlanPath = Join-Path $ExtensionRoot 'implementation-plan.json'
$humanPlanPath = Join-Path $ExtensionRoot 'implementation-plan.md'
Assert-True `
    (Test-Path -LiteralPath $humanPlanPath -PathType Leaf) `
    'The adjacent human-readable implementation-plan projection is absent.'
$humanPlan = Get-Content -LiteralPath $humanPlanPath -Raw
$canonicalPlanDigest = Get-Digest $canonicalPlanPath
Assert-True `
    ($humanPlan.Contains(
        'Non-authoritative human-readable projection. The canonical source is')) `
    'The human-readable implementation plan is not explicitly non-authoritative.'
Assert-True `
    ($humanPlan.Contains(
        "Canonical SHA-256: ``sha256:$canonicalPlanDigest``")) `
    'The human-readable implementation plan does not bind the current canonical plan digest.'

$fixtureIds = @($fixtures.fixtures | ForEach-Object { $_.fixtureId })
Assert-True `
    ($fixtureIds.Count -eq 42) `
    'The acceptance catalog does not contain exactly 42 fixtures.'
Assert-True `
    (($fixtureIds | Sort-Object -Unique).Count -eq 42) `
    'The acceptance fixture IDs are not unique.'
$profileFixtureIds = @(
    $fixtures.evidenceProfiles |
        ForEach-Object { $_.requiredFixtureIds } |
        ForEach-Object { $_ }
)
Assert-True `
    ($profileFixtureIds.Count -eq 42) `
    'The evidence profiles do not reference exactly 42 fixtures.'
Assert-True `
    ($null -eq (Compare-Object $fixtureIds $profileFixtureIds)) `
    'The evidence profiles do not cover every fixture exactly once.'
Assert-True `
    ($providerEvidence.artifactVersion -eq '3.0.0') `
    'Provider evidence is not the converged 3.0.0 review candidate.'

Assert-True `
    ($manifest.reviewState -eq 'approved') `
    'The review manifest is not approved.'
Assert-True `
    ($manifest.implementationStatus -eq 'not-started') `
    'The review manifest must keep implementation not-started.'
Assert-True `
    ($null -ne $manifest.approvalRecord) `
    'The review manifest does not reference the supplied approval record.'
Assert-True `
    ($approval.decision -eq 'approved' -and
        $approval.conditions.Count -eq 0 -and
        $approval.supersession.state -eq 'active' -and
        $null -eq $approval.supersession.supersededBy) `
    'The approval record is not an active, unconditional approval.'
Assert-True `
    ($approval.design.digest -eq
        'sha256:a44f13b3a34fb01b6c336ba2069cef9278f3f4bc27d9e128f5df05cf30c66592' -and
        $approval.plan.digest -eq
        'sha256:0ee9304510bbfaa6de508bf4fd5f0726625cb33e77aced26cbfe5a15db72c5a3') `
    'The approval record does not bind the exact reviewed design and plan.'
Assert-True `
    ($approvalAuthority.humanDecisionSource.statement -eq
        'I approve implementation' -and
        $approvalAuthority.humanDecisionSource.statementSha256 -eq
        'sha256:48e5abeea77f2cb8f2078bd433b051ee1069f56699d5962a3c44f05fca827322') `
    'The approval authority source does not bind the exact human statement.'
Assert-DigestReference `
    $approval.authority.source `
    'extensions/development-tools/approval-authority-source.json' `
    'The approval record does not bind the current authority-source bytes.'
Assert-True `
    ($manifest.approvalRecord.sha256 -eq
        (Get-RepositoryDigest 'extensions/development-tools/design-plan-approval.json') -and
        $manifest.approvalRecord.authoritySourceSha256 -eq
        (Get-RepositoryDigest 'extensions/development-tools/approval-authority-source.json')) `
    'The review manifest does not bind the exact approval artifacts.'

$manifestPaths = @($manifest.artifacts | ForEach-Object { $_.path })
Assert-True `
    (($manifestPaths | Sort-Object -Unique).Count -eq $manifestPaths.Count) `
    'The review manifest contains duplicate artifact paths.'
foreach ($artifact in $manifest.artifacts) {
    $artifactPath = Join-Path $repositoryRoot $artifact.path
    Assert-True `
        (Test-Path -LiteralPath $artifactPath -PathType Leaf) `
        "Review artifact $($artifact.path) is missing."
    Assert-True `
        ($artifact.sha256 -eq (Get-Digest $artifactPath)) `
        "Review artifact $($artifact.path) does not match its manifest digest."
}

$planDigestBefore = Get-Digest $canonicalPlanPath
$humanPlanDigestBefore = Get-Digest $humanPlanPath
& (Join-Path $ExtensionRoot 'materialize-implementation-plan.ps1') `
    -ExtensionRoot $ExtensionRoot |
    Out-Null
$planDigestAfterOne = Get-Digest $canonicalPlanPath
$humanPlanDigestAfterOne = Get-Digest $humanPlanPath
& (Join-Path $ExtensionRoot 'materialize-implementation-plan.ps1') `
    -ExtensionRoot $ExtensionRoot |
    Out-Null
$planDigestAfterTwo = Get-Digest $canonicalPlanPath
$humanPlanDigestAfterTwo = Get-Digest $humanPlanPath
Assert-True `
    ($planDigestBefore -eq $planDigestAfterOne -and
        $planDigestAfterOne -eq $planDigestAfterTwo) `
    'The implementation-plan materializer is not byte-deterministic.'
Assert-True `
    ($humanPlanDigestBefore -eq $humanPlanDigestAfterOne -and
        $humanPlanDigestAfterOne -eq $humanPlanDigestAfterTwo) `
    'The human-readable implementation-plan projection is not byte-deterministic.'

Write-Output 'Development Tools review set validation passed.'
