param(
    [string] $ExtensionRoot = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$requiredFiles = @(
    'README.md',
    'prior-draft-assessment.md',
    'design-intent.md',
    'architecture-design.json',
    'architecture-design.md',
    'static-conformance-disposition.md',
    'implementation-plan.json',
    'implementation-plan.md',
    'materialize-implementation-plan.ps1',
    'validate-review-set.ps1',
    'validation-report.md',
    'approval-authority-source.json',
    'design-plan-approval.json',
    'review-manifest.json'
)

function Assert-Condition([bool] $condition, [string] $message) {
    if (-not $condition) {
        throw $message
    }
}

function Digest([string] $path) {
    return (
        Get-FileHash -Algorithm SHA256 -LiteralPath $path
    ).Hash.ToLowerInvariant()
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

$designPath = Join-Path $ExtensionRoot 'architecture-design.json'
$planPath = Join-Path $ExtensionRoot 'implementation-plan.json'
$intentPath = Join-Path $ExtensionRoot 'design-intent.md'
$designMarkdownPath = Join-Path $ExtensionRoot 'architecture-design.md'
$planMarkdownPath = Join-Path $ExtensionRoot 'implementation-plan.md'
$dispositionPath = Join-Path `
    $ExtensionRoot `
    'static-conformance-disposition.md'
$authorityPath = Join-Path $ExtensionRoot 'approval-authority-source.json'
$approvalPath = Join-Path $ExtensionRoot 'design-plan-approval.json'

$design = Get-Content -LiteralPath $designPath -Raw | ConvertFrom-Json
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$manifest = Get-Content `
    -LiteralPath (Join-Path $ExtensionRoot 'review-manifest.json') `
    -Raw |
    ConvertFrom-Json
$designMarkdown = [IO.File]::ReadAllText($designMarkdownPath)
$planMarkdown = [IO.File]::ReadAllText($planMarkdownPath)
$intent = [IO.File]::ReadAllText($intentPath)
$disposition = [IO.File]::ReadAllText($dispositionPath)
$authority = Get-Content -LiteralPath $authorityPath -Raw | ConvertFrom-Json
$approval = Get-Content -LiteralPath $approvalPath -Raw | ConvertFrom-Json
$designDigest = Digest $designPath
$planDigest = Digest $planPath

Assert-Condition (
    $design.title -eq 'Program Kit reusable consumer-owned C# build gates'
) 'Unexpected architecture design title.'
Assert-Condition (
    $plan.design.identity -eq
        'pkid:design:program-kit:reusable-csharp-build-gates' -and
    $plan.design.version -eq '1.0.0' -and
    $plan.design.digest -eq ('sha256:' + $designDigest)
) 'The plan does not bind the exact canonical design bytes.'
Assert-Condition (
    $plan.state -eq 'ready-for-human-decision' -and
    $plan.unresolvedDecisions.Count -eq 0
) 'The plan is not ready for one exact human decision.'

$requirementIds = @($plan.requirementIds)
$workUnits = @($plan.workUnits)
$trace = @($plan.trace)
Assert-Condition ($requirementIds.Count -eq 32) (
    "Expected 32 requirements; observed $($requirementIds.Count).")
Assert-Condition (
    @($requirementIds | Sort-Object -Unique).Count -eq
        $requirementIds.Count
) 'Requirement IDs are not unique.'
Assert-Condition ($workUnits.Count -eq 11) (
    "Expected 11 work units; observed $($workUnits.Count).")
Assert-Condition (
    @($workUnits.workUnitId | Sort-Object -Unique).Count -eq
        $workUnits.Count
) 'Work-unit IDs are not unique.'
Assert-Condition ($trace.Count -eq $requirementIds.Count) (
    'Requirement trace cardinality does not match requirements.')

$workUnitById = @{}
foreach ($workUnit in $workUnits) {
    $workUnitById[$workUnit.workUnitId] = $workUnit
}
foreach ($workUnit in $workUnits) {
    foreach ($dependency in @($workUnit.dependsOn)) {
        Assert-Condition $workUnitById.ContainsKey($dependency) (
            "Unknown dependency '$dependency'.")
        Assert-Condition (
            $workUnitById[$dependency].sequence -lt $workUnit.sequence
        ) "Dependency '$dependency' does not precede '$($workUnit.workUnitId)'."
    }
}

$tracedIds = @($trace.requirementId | Sort-Object)
Assert-Condition (
    -not (Compare-Object ($requirementIds | Sort-Object) $tracedIds)
) 'Requirement trace identities do not exactly match requirement IDs.'
foreach ($entry in $trace) {
    Assert-Condition (@($entry.workUnitIds).Count -gt 0) (
        "Requirement '$($entry.requirementId)' has no work unit.")
    foreach ($workUnitId in @($entry.workUnitIds)) {
        Assert-Condition $workUnitById.ContainsKey($workUnitId) (
            "Requirement '$($entry.requirementId)' names unknown '$workUnitId'.")
    }
}

$requirementRows = [regex]::Matches(
    $planMarkdown,
    '(?m)^\|\s*`PKCG-R\d{3}`\s*\|')
$workUnitHeadings = [regex]::Matches(
    $planMarkdown,
    '(?m)^### `PKCG-W\d{3}`')
Assert-Condition ($requirementRows.Count -eq 32) (
    'Markdown requirement count differs from canonical plan.')
Assert-Condition ($workUnitHeadings.Count -eq 11) (
    'Markdown work-unit count differs from canonical plan.')

$projectionMarkers = @(
    'StaticConformanceDisposition',
    'program-kit-public-contract',
    'consumer-owned',
    'temporary activation exception',
    'gate-establishment',
    'Orbyss.ProgramKit.CSharpGate',
    'PKCC',
    'PKCS',
    'PKCG',
    'design-csharp-build-gate',
    'implement-software-plan'
)
foreach ($marker in $projectionMarkers) {
    Assert-Condition (
        $designMarkdown.Contains($marker) -and
        (
            (Get-Content -LiteralPath $designPath -Raw).Contains($marker) -or
            $planMarkdown.Contains($marker) -or
            $intent.Contains($marker)
        )
    ) "Projection marker '$marker' is not represented consistently."
}

foreach ($path in @(
    $intentPath,
    $designMarkdownPath,
    $planMarkdownPath,
    $dispositionPath
)) {
    $text = [IO.File]::ReadAllText($path)
    Assert-Condition (
        -not [regex]::IsMatch(
            $text,
            '\bdomain[- ]analy[sz]er',
            [Text.RegularExpressions.RegexOptions]::IgnoreCase)
    ) "Forbidden terminology appears in '$(Split-Path $path -Leaf)'."
}

Assert-Condition (
    $intent.Contains(
        'Program Kit public contract-conformance diagnostics remain single-sourced')
) 'Intent omits public contract diagnostic ownership.'
Assert-Condition (
    $designMarkdown.Contains(
        'Only explicitly selected analyzer components run on consumer-owned source')
) 'Design omits exact selected analyzer composition.'
Assert-Condition (
    $designMarkdown.Contains(
        'No environment-variable switch, command-line skip flag')
) 'Design omits the ambient temporary-exception bypass prohibition.'
Assert-Condition (
    $disposition.Contains('Candidate disposition: `reuse-existing`') -and
    $disposition.Contains('Temporary activation exceptions: none')
) 'The extension static-conformance candidate is incomplete.'

$intentDigest = Digest $intentPath
$intentReferences = @(
    $design.sourceTruthAuthorities |
        Where-Object {
            $_.source.identity -eq
                'pkid:intent:program-kit:reusable-csharp-build-gates'
        }
)
Assert-Condition ($intentReferences.Count -eq 1) (
    'Canonical design must contain one exact intent authority.')
Assert-Condition (
    $intentReferences[0].source.digest -eq ('sha256:' + $intentDigest)
) 'Canonical design intent digest is stale.'

$repositoryRoot = [IO.Path]::GetFullPath(
    (Join-Path $ExtensionRoot '..\..'))
Assert-Condition (
    $manifest.reviewState -eq 'approved' -and
    $manifest.approvalRecord.path -eq
        'extensions/reusable-csharp-build-gates/design-plan-approval.json' -and
    $manifest.approvalRecord.sha256 -eq (Digest $approvalPath) -and
    $manifest.approvalRecord.authoritySourceSha256 -eq
        (Digest $authorityPath)
) 'Review manifest does not bind the exact approval evidence.'
Assert-Condition (
    $authority.design.digest -eq ('sha256:' + $designDigest) -and
    $authority.plan.digest -eq ('sha256:' + $planDigest) -and
    $authority.humanDecisionSource.statementSha256 -eq
        'sha256:7a5390aaa5067ffb4d3cb5961c6ad97f8665a970df8336513186b6def2b4400e'
) 'Approval authority does not bind the exact design, plan, and statement.'
Assert-Condition (
    $approval.decision -eq 'approved' -and
    @($approval.conditions).Count -eq 0 -and
    $approval.supersession.state -eq 'active' -and
    $approval.design.digest -eq ('sha256:' + $designDigest) -and
    $approval.plan.digest -eq ('sha256:' + $planDigest) -and
    $approval.authority.source.digest -eq
        ('sha256:' + (Digest $authorityPath))
) 'Approval record is not an active unconditional exact-byte approval.'
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
    Assert-Condition ((Digest $artifactPath) -eq $artifact.sha256) (
        "Manifest digest is stale for '$($artifact.path)'.")
}

Write-Output 'PASS files-present-lf-no-bom'
Write-Output 'PASS json-syntax-and-exact-design-binding'
Write-Output 'PASS requirements-work-units-dependency-order-and-trace'
Write-Output 'PASS manual-design-projection-markers'
Write-Output 'PASS analyzer-ownership-and-terminology'
Write-Output 'PASS static-conformance-candidate'
Write-Output 'PASS exact-intent-digest'
Write-Output 'PASS exact-human-approval-and-artifact-digests'
