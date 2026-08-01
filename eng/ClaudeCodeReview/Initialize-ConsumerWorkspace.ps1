[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $ReviewKit,
    [Parameter(Mandatory = $true)] [string] $ConsumerRoot
)

$ErrorActionPreference = 'Stop'
$pkKit = (Resolve-Path -LiteralPath $ReviewKit).Path
$pkManifestPath = Join-Path $pkKit 'manifest.json'
$pkManifest = Get-Content -Raw -LiteralPath $pkManifestPath | ConvertFrom-Json -Depth 20
if ($pkManifest.schema -ne 'program-kit.claude-code-review-kit/v1') { throw 'The review-kit schema is unsupported.' }
foreach ($pkFile in $pkManifest.files) {
    $pkPath = [IO.Path]::GetFullPath((Join-Path $pkKit $pkFile.logicalPath))
    if (-not $pkPath.StartsWith($pkKit + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'A review-kit path escapes the sealed root.' }
    if (-not (Test-Path -LiteralPath $pkPath -PathType Leaf)) { throw "Missing sealed review-kit file: $($pkFile.logicalPath)" }
    $pkDigest = 'sha256:' + (Get-FileHash -LiteralPath $pkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($pkDigest -ne $pkFile.digest) { throw "Review-kit digest mismatch: $($pkFile.logicalPath)" }
}

$pkConsumer = [IO.Path]::GetFullPath($ConsumerRoot)
if (Test-Path -LiteralPath $pkConsumer) {
    if (@(Get-ChildItem -LiteralPath $pkConsumer -Force).Count -gt 0) { throw 'The isolated consumer root must be absent or empty.' }
}
else { New-Item -ItemType Directory -Path $pkConsumer | Out-Null }

$pkContaminants = @('.program-kit-source.json', '.specify', '.agents/skills/program-kit', '.program-kit/session-integrations')
foreach ($pkRelative in $pkContaminants) {
    if (Test-Path -LiteralPath (Join-Path $pkConsumer $pkRelative)) { throw "Isolated boundary contamination: $pkRelative" }
}
git -C $pkConsumer init --quiet
if ($LASTEXITCODE -ne 0) { throw 'Could not initialize the isolated consumer repository.' }

$pkEnvironment = [ordered]@{
    schema = 'program-kit.claude-code-environment/v1'
    osFamily = $(if ($IsWindows) { 'windows' } else { 'linux' })
    osArchitecture = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    cleanBoundaryPassed = $true
    sourceAbsent = $true
    specKitAbsent = $true
    codexProjectionAbsent = $true
    priorSessionStateAbsent = $true
    reviewKitDigest = $pkManifest.reviewKitDigest
    supportClaim = $pkManifest.supportClaim
    canonicalDependencyStatus = $pkManifest.canonicalDependencyStatus
}
$pkEnvironment | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $pkConsumer 'environment.json') -Encoding utf8NoBOM
Write-Output ($pkEnvironment | ConvertTo-Json -Depth 10 -Compress)
