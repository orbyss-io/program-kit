[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ConsumerRoot
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$consumer = (Resolve-Path -LiteralPath $ConsumerRoot).Path
if ($consumer -eq $repositoryRoot -or $consumer.StartsWith($repositoryRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The Codex review seed must be an isolated consumer workspace outside Program Kit source.'
}
if (Test-Path -LiteralPath (Join-Path $consumer '.program-kit-source.json')) {
    throw 'The selected workspace is marked as Program Kit source.'
}
foreach ($generatedRoot in @('products', 'components', 'feeds')) {
    if (Test-Path -LiteralPath (Join-Path $consumer $generatedRoot)) {
        throw "The consumer already contains '$generatedRoot'; use a clean installed session workspace for the review seed."
    }
}

$contractPath = Join-Path $repositoryRoot 'specs/002-session-integration-proof/contracts/codex-session-review-seed.json'
$contract = Get-Content -LiteralPath $contractPath -Raw | ConvertFrom-Json -Depth 100
$fixtureRoot = Join-Path $repositoryRoot 'tests/Fixtures/Reference.Status/Valid'
foreach ($file in $contract.files) {
    $logicalPath = [string]$file.logicalPath
    $source = [IO.Path]::GetFullPath((Join-Path $fixtureRoot $logicalPath))
    $target = [IO.Path]::GetFullPath((Join-Path $consumer $logicalPath))
    $sourceDigest = 'sha256:' + (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sourceDigest -cne [string]$file.digest) { throw "The repository fixture is stale relative to the review-seed contract: $logicalPath" }
    if (Test-Path -LiteralPath $target) {
        $targetDigest = 'sha256:' + (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($targetDigest -cne $sourceDigest) { throw "The consumer already has different bytes at '$logicalPath'." }
        continue
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
}

$programKitLogicalPath = if ($IsWindows) { '.program-kit/tools/program-kit.exe' } else { '.program-kit/tools/program-kit' }
$dynamicPaths = [ordered]@{
    cli = $programKitLogicalPath
    projection = '.agents/skills/program-kit/SKILL.md'
    installationRecord = '.program-kit/session-integrations/codex/installation.json'
}
foreach ($path in $dynamicPaths.Values) {
    if (-not (Test-Path -LiteralPath (Join-Path $consumer $path) -PathType Leaf)) {
        throw "The consumer is not ready for live review; missing '$path'. Complete exact session installation first."
    }
}
$installation = Get-Content -LiteralPath (Join-Path $consumer $dynamicPaths.installationRecord) -Raw | ConvertFrom-Json -Depth 100
$dynamicArtifacts = [ordered]@{}
foreach ($property in $dynamicPaths.GetEnumerator()) {
    $path = Join-Path $consumer $property.Value
    $dynamicArtifacts[$property.Key] = [ordered]@{
        logicalPath = $property.Value
        digest = 'sha256:' + (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$packetPath = Join-Path $consumer '.program-kit/review/codex-session-review-packet.json'
New-Item -ItemType Directory -Path (Split-Path -Parent $packetPath) -Force | Out-Null
[ordered]@{
    schema = 'program-kit.codex-session-review-packet/v1'
    canonicalProfile = 'program-kit.canonical-json/v1'
    scenarioIdentity = $contract.scenarioIdentity
    seedContractDigest = 'sha256:' + (Get-FileHash -LiteralPath $contractPath -Algorithm SHA256).Hash.ToLowerInvariant()
    installationIdentity = $installation.installationIdentity
    definition = $installation.definition
    provider = $installation.provider
    cliRelease = $installation.cliRelease
    dynamicArtifacts = $dynamicArtifacts
} | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $packetPath -Encoding utf8NoBOM

$preflight = & (Join-Path $PSScriptRoot 'Assert-CodexSessionReviewSeed.ps1') -SeedRoot $consumer
if ($LASTEXITCODE -ne 0) { throw 'The initialized Codex session-review seed failed its read-only preflight.' }
Write-Host 'Codex session-review seed initialized and preflighted.'
Write-Output $preflight
