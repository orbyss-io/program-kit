[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$amendmentRoot = $PSScriptRoot
$reviewSetRoot = [IO.Path]::GetFullPath((Join-Path $amendmentRoot '..\..'))
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $amendmentRoot '..\..\..\..'))
$utf8 = [Text.UTF8Encoding]::new($false, $true)

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
        "Relocated artifact has a UTF-8 byte-order mark: $path"
    $text = $utf8.GetString($bytes)
    $normalized = $text.Replace("`r`n", "`n").Replace("`r", "`n")
    $normalizedBytes = [Text.UTF8Encoding]::new($false).GetBytes($normalized)
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($normalizedBytes)
    ).ToLowerInvariant()
}

$map = Get-Content `
    -LiteralPath (Join-Path $amendmentRoot 'relocation-map.json') `
    -Raw |
    ConvertFrom-Json -Depth 20
$manifestPath = Join-Path $reviewSetRoot 'review-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw |
    ConvertFrom-Json -Depth 100

Assert-True `
    ($map.sourceMainCommit -eq
        '11978dc6f3cbd66cd204214318eb166cb02c3e1c') `
    'The relocation amendment does not bind the exact layout main commit.'
Assert-True `
    ($manifest.reviewSetId -eq $map.frozenReviewSet.identity -and
        $manifest.reviewSetVersion -eq $map.frozenReviewSet.version) `
    'The relocation amendment and frozen review manifest differ.'
Assert-True `
    ($manifest.approvalBoundary.candidateDesignSha256 -eq
        $map.frozenReviewSet.designSha256.Substring(7) -and
        $manifest.approvalBoundary.candidatePlanSha256 -eq
        $map.frozenReviewSet.planSha256.Substring(7)) `
    'The relocation amendment does not bind the frozen design and plan.'
Assert-True `
    ($manifest.approvalRecord.sha256 -eq
        $map.frozenReviewSet.approvalSha256.Substring(7)) `
    'The relocation amendment does not bind the frozen approval record.'

$historicalPrefix = [string] $map.resolution.historicalPrefix
$livePrefix = [string] $map.resolution.livePrefix
$seen = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal)
foreach ($artifact in $manifest.artifacts) {
    $historicalPath = [string] $artifact.path
    Assert-True `
        ($historicalPath.StartsWith(
            $historicalPrefix,
            [StringComparison]::Ordinal)) `
        "Undeclared historical path prefix: $historicalPath"
    Assert-True `
        ($seen.Add($historicalPath)) `
        "Duplicate historical artifact path: $historicalPath"
    $suffix = $historicalPath.Substring($historicalPrefix.Length)
    Assert-True `
        (-not [string]::IsNullOrWhiteSpace($suffix) -and
            -not $suffix.Contains('..') -and
            -not $suffix.Contains('\')) `
        "Unsafe relocated artifact suffix: $historicalPath"
    $liveRelativePath = $livePrefix + $suffix
    $livePath = [IO.Path]::GetFullPath(
        (Join-Path $repositoryRoot $liveRelativePath))
    Assert-True `
        ($livePath.StartsWith(
            $reviewSetRoot + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) `
        "Relocated artifact escapes the review-set root: $historicalPath"
    Assert-True `
        (Test-Path -LiteralPath $livePath -PathType Leaf) `
        "Relocated artifact is missing: $liveRelativePath"
    Assert-True `
        ((Get-LfDigest $livePath) -eq [string] $artifact.sha256) `
        "Relocated artifact digest differs: $liveRelativePath"
}

Assert-True `
    (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot 'extensions'))) `
    'The removed root extensions directory was reintroduced.'

Write-Output 'Development Tools review relocation validation passed.'
