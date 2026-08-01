[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $ReviewKit,
    [Parameter(Mandatory = $true)] [string] $ConsumerRoot,
    [ValidateSet('accepted', 'rejected', 'pending')] [string] $Decision = 'pending',
    [Parameter(Mandatory = $true)] [string] $ReviewerIdentity
)

$ErrorActionPreference = 'Stop'
$pkKit = (Resolve-Path -LiteralPath $ReviewKit).Path
$pkConsumer = (Resolve-Path -LiteralPath $ConsumerRoot).Path
$pkManifest = Get-Content -Raw -LiteralPath (Join-Path $pkKit 'manifest.json') | ConvertFrom-Json -Depth 20
$pkEvidenceRoot = Join-Path $pkConsumer '.program-kit/evidence'
$pkDeterministicPath = Join-Path $pkEvidenceRoot 'claude-deterministic-proof.json'
$pkLivePath = Join-Path $pkEvidenceRoot 'claude-live-trials.json'

if ($Decision -eq 'accepted') {
    if ($pkManifest.canonicalDependencyStatus -ne 'accepted' -or $pkManifest.supportClaim -ne 'supported') { throw 'Accepted review is forbidden while the canonical dependency or support claim is not accepted.' }
    if (-not (Test-Path -LiteralPath $pkDeterministicPath) -or -not (Test-Path -LiteralPath $pkLivePath)) { throw 'Accepted review requires complete deterministic and live evidence.' }
    $pkDeterministic = Get-Content -Raw -LiteralPath $pkDeterministicPath | ConvertFrom-Json -Depth 20
    $pkLive = Get-Content -Raw -LiteralPath $pkLivePath | ConvertFrom-Json -Depth 20
    if ($pkDeterministic.failed -ne 0 -or $pkDeterministic.passed -ne 10 -or @($pkLive.trials).Count -ne 10 -or @($pkLive.trials | Where-Object status -ne 'passed').Count -ne 0) {
        throw 'Accepted review requires ten complete passing deterministic and live trials.'
    }
}

New-Item -ItemType Directory -Path $pkEvidenceRoot -Force | Out-Null
$pkLimitations = @()
if ($pkManifest.canonicalDependencyStatus -ne 'accepted') { $pkLimitations += 'feature-002-product-acceptance-rejected' }
if (-not (Test-Path -LiteralPath $pkLivePath)) { $pkLimitations += 'live-claude-review-not-executed' }
$pkRecord = [ordered]@{
    schema = 'program-kit.claude-code-human-review/v1'
    reviewKitDigest = $pkManifest.reviewKitDigest
    provider = $pkManifest.provider
    adapter = $pkManifest.adapter
    reviewerIdentity = $ReviewerIdentity
    humanDecision = $Decision
    deterministicEvidencePresent = (Test-Path -LiteralPath $pkDeterministicPath)
    liveEvidencePresent = (Test-Path -LiteralPath $pkLivePath)
    limitations = $pkLimitations
}
$pkRecord | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $pkEvidenceRoot 'human-review.json') -Encoding utf8NoBOM
Write-Output ($pkRecord | ConvertTo-Json -Depth 20 -Compress)
