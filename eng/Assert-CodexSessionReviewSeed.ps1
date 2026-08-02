[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $SeedRoot,

    [string] $ContractPath = 'specs/002-session-integration-proof/contracts/codex-session-review-seed.json',

    [string] $PacketPath = '.program-kit/review/codex-session-review-packet.json',

    [switch] $StaticOnly
)

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw 'Codex session review requires PowerShell 7 or later. Open PowerShell 7 with pwsh and rerun the command.'
}

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$seed = (Resolve-Path -LiteralPath $SeedRoot).Path
$emptyDigest = 'sha256:' + ('0' * 64)

function Get-ByteDigest {
    param([Parameter(Mandatory = $true)][string] $Path)
    return 'sha256:' + (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Resolve-SeedFile {
    param([Parameter(Mandatory = $true)][string] $LogicalPath)
    if ([IO.Path]::IsPathRooted($LogicalPath) -or $LogicalPath.Contains('..', [StringComparison]::Ordinal)) {
        throw "Review-seed logical path is unsafe: $LogicalPath"
    }
    $candidate = [IO.Path]::GetFullPath((Join-Path $seed $LogicalPath))
    if (-not $candidate.StartsWith($seed + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Review-seed logical path escapes the seed root: $LogicalPath"
    }
    return $candidate
}

function Assert-ExactIdentity {
    param(
        [Parameter(Mandatory = $true)] $Observed,
        [Parameter(Mandatory = $true)] $Expected,
        [Parameter(Mandatory = $true)][string] $Subject
    )
    foreach ($field in @('authority', 'kind', 'name', 'revision', 'digest')) {
        if ([string]$Observed.$field -cne [string]$Expected.$field) {
            throw "$Subject does not match the exact current identity."
        }
    }
}

function Assert-DependencyMirror {
    param([Parameter(Mandatory = $true)] $Binding)

    $logicalPath = [string]$Binding.logicalPath
    $mirror = Resolve-SeedFile -LogicalPath $logicalPath
    if (-not (Test-Path -LiteralPath $mirror -PathType Container)) {
        throw 'The review-seed dependency mirror is missing.'
    }
    if ((Get-Item -LiteralPath $mirror -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'The review-seed dependency mirror must not be a reparse point.'
    }

    $lockPath = Join-Path $mirror 'mirror.lock.json'
    if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
        throw 'The review-seed dependency mirror lock is missing.'
    }
    if ((Get-Item -LiteralPath $lockPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'The review-seed dependency mirror lock must not be a reparse point.'
    }
    $lockDigest = Get-ByteDigest -Path $lockPath
    if ($lockDigest -cne [string]$Binding.lockDigest) {
        throw 'The review-seed dependency mirror lock is stale or mismatched.'
    }
    $lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json -Depth 100
    if ($lock.schema -cne 'program-kit.dependency-mirror-lock/v1' -or @($lock.packages).Count -eq 0) {
        throw 'The review-seed dependency mirror lock contract is unsupported.'
    }

    $expectedNames = @('mirror.lock.json')
    foreach ($package in $lock.packages) {
        $fileName = (([string]$package.id).ToLowerInvariant() + '.' + [string]$package.version + '.nupkg')
        $expectedNames += $fileName
        $packagePath = Join-Path $mirror $fileName
        if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf) -or
            ((Get-Item -LiteralPath $packagePath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            (Get-ByteDigest -Path $packagePath) -cne [string]$package.sha256) {
            throw "The review-seed dependency mirror artifact is missing or changed: $fileName"
        }
    }
    if (@($expectedNames | Sort-Object -Unique).Count -ne $expectedNames.Count) {
        throw 'The review-seed dependency mirror contains duplicate package identities.'
    }
    if (@(Get-ChildItem -LiteralPath $mirror -Force -Directory).Count -ne 0) {
        throw 'The review-seed dependency mirror contains undeclared directories.'
    }
    $actualNames = @(Get-ChildItem -LiteralPath $mirror -Force -File | ForEach-Object { $_.Name } | Sort-Object -CaseSensitive)
    $sortedExpected = @($expectedNames | Sort-Object -CaseSensitive)
    if (Compare-Object -ReferenceObject $sortedExpected -DifferenceObject $actualNames -CaseSensitive) {
        throw 'The review-seed dependency mirror contains undeclared, missing, or case-colliding artifacts.'
    }

    return [ordered]@{
        logicalPath = $logicalPath
        lockDigest = $lockDigest
        fileCount = $actualNames.Count
    }
}

$contract = if ([IO.Path]::IsPathRooted($ContractPath)) {
    [IO.Path]::GetFullPath($ContractPath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $repositoryRoot $ContractPath))
}
if (-not (Test-Path -LiteralPath $contract -PathType Leaf)) { throw 'The checked-in Codex review-seed contract is missing.' }
$contractText = Get-Content -LiteralPath $contract -Raw
if ($contractText.Contains($emptyDigest, [StringComparison]::Ordinal)) { throw 'The review-seed contract contains a zero digest.' }
$seedContract = $contractText | ConvertFrom-Json -Depth 100
if ($seedContract.schema -cne 'program-kit.codex-session-review-seed/v1' -or
    $seedContract.canonicalProfile -cne 'program-kit.canonical-json/v1') {
    throw 'The review-seed contract schema or canonical profile is unsupported.'
}
if (@($seedContract.files).Count -ne 9) { throw 'The review-seed contract must contain the exact nine-file factory closure.' }

$observedPaths = @($seedContract.files | ForEach-Object { [string]$_.logicalPath })
if (@($observedPaths | Sort-Object -CaseSensitive -Unique).Count -ne $observedPaths.Count) {
    throw 'The review-seed contract contains duplicate logical paths.'
}
foreach ($file in $seedContract.files) {
    $path = Resolve-SeedFile -LogicalPath ([string]$file.logicalPath)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "The live review seed is missing '$($file.logicalPath)'." }
    if ((Get-Content -LiteralPath $path -Raw).Contains($emptyDigest, [StringComparison]::Ordinal)) {
        throw "The live review seed contains a zero digest at '$($file.logicalPath)'."
    }
    $observedDigest = Get-ByteDigest -Path $path
    if ($observedDigest -cne [string]$file.digest) { throw "The live review seed has stale or mismatched bytes at '$($file.logicalPath)'." }
}
$dependencyMirror = Assert-DependencyMirror -Binding $seedContract.dependencyMirror

$construct = Get-Content -LiteralPath (Resolve-SeedFile 'requests/construct.json') -Raw | ConvertFrom-Json -Depth 100
$grant = Get-Content -LiteralPath (Resolve-SeedFile 'authority/construct-grant.json') -Raw | ConvertFrom-Json -Depth 100
$explain = Get-Content -LiteralPath (Resolve-SeedFile 'requests/explain.json') -Raw | ConvertFrom-Json -Depth 100
$evaluate = Get-Content -LiteralPath (Resolve-SeedFile 'requests/evaluate.json') -Raw | ConvertFrom-Json -Depth 100
$expectedByPath = @{}
foreach ($file in $seedContract.files) { $expectedByPath[[string]$file.logicalPath] = [string]$file.digest }
if ($explain.operation -cne 'explain' -or $construct.operation -cne 'construct' -or $evaluate.operation -cne 'evaluate') {
    throw 'The review-seed operation sequence is not the exact explain/construct/evaluate scenario.'
}
if ($construct.authorityGrant.logicalPath -cne 'authority/construct-grant.json' -or
    $construct.authorityGrant.digest -cne $expectedByPath['authority/construct-grant.json']) {
    throw 'The construct request does not bind the exact current authority grant.'
}
if ($grant.provenance.logicalPath -cne 'authority/review.json' -or
    $grant.provenance.digest -cne $expectedByPath['authority/review.json']) {
    throw 'The authority grant does not bind the exact review record.'
}
if ($grant.revocationReference.logicalPath -cne 'authority/revocations.json' -or
    $grant.revocationReference.digest -cne $expectedByPath['authority/revocations.json']) {
    throw 'The authority grant does not bind the exact revocation state.'
}

if ($StaticOnly) {
    [ordered]@{
        schema = 'program-kit.codex-session-review-preflight/v1'
        status = 'ready'
        scenarioIdentity = $seedContract.scenarioIdentity
        seedContractDigest = Get-ByteDigest -Path $contract
        staticFileCount = @($seedContract.files).Count
        dependencyMirror = $dependencyMirror
        constructAuthorityGrant = [ordered]@{
            logicalPath = [string]$construct.authorityGrant.logicalPath
            digest = [string]$construct.authorityGrant.digest
        }
    } | ConvertTo-Json -Compress
    return
}

if (Test-Path -LiteralPath (Join-Path $seed '.program-kit-source.json')) {
    throw 'The selected workspace is marked as Program Kit source and cannot host the consumer review.'
}
$packet = Resolve-SeedFile -LogicalPath $PacketPath
if (-not (Test-Path -LiteralPath $packet -PathType Leaf)) { throw 'The bound Codex session-review packet is missing.' }
$packetText = Get-Content -LiteralPath $packet -Raw
if ($packetText.Contains($emptyDigest, [StringComparison]::Ordinal)) { throw 'The bound Codex session-review packet contains a zero digest.' }
$reviewPacket = $packetText | ConvertFrom-Json -Depth 100
if ($reviewPacket.schema -cne 'program-kit.codex-session-review-packet/v1' -or
    $reviewPacket.canonicalProfile -cne 'program-kit.canonical-json/v1' -or
    $reviewPacket.scenarioIdentity -cne $seedContract.scenarioIdentity -or
    $reviewPacket.seedContractDigest -cne (Get-ByteDigest -Path $contract)) {
    throw 'The Codex session-review packet is stale or bound to a different scenario or seed contract.'
}
if ([string]$reviewPacket.dependencyMirror.logicalPath -cne [string]$dependencyMirror.logicalPath -or
    [string]$reviewPacket.dependencyMirror.lockDigest -cne [string]$dependencyMirror.lockDigest -or
    [int]$reviewPacket.dependencyMirror.fileCount -ne [int]$dependencyMirror.fileCount) {
    throw "The Codex session-review packet's dependency-mirror binding is stale or mismatched."
}

$programKitLogicalPath = if ($IsWindows) { '.program-kit/tools/program-kit.exe' } else { '.program-kit/tools/program-kit' }
$dynamicFiles = [ordered]@{
    cli = $programKitLogicalPath
    projection = '.agents/skills/program-kit/SKILL.md'
    installationRecord = '.program-kit/session-integrations/codex/installation.json'
}
foreach ($property in $dynamicFiles.GetEnumerator()) {
    $path = Resolve-SeedFile -LogicalPath $property.Value
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "The review seed is missing its bound $($property.Key)." }
    if ([string]$reviewPacket.dynamicArtifacts.($property.Key).logicalPath -cne $property.Value -or
        [string]$reviewPacket.dynamicArtifacts.($property.Key).digest -cne (Get-ByteDigest -Path $path)) {
        throw "The review packet's $($property.Key) binding is stale or mismatched."
    }
}

$installation = Get-Content -LiteralPath (Resolve-SeedFile '.program-kit/session-integrations/codex/installation.json') -Raw | ConvertFrom-Json -Depth 100
$currentDefinition = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/ProgramKit.SessionIntegration/Resources/session-integration-definition.json') -Raw | ConvertFrom-Json -Depth 100
$currentProvider = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/ProgramKit.SessionIntegration.Providers.Codex/Resources/codex-provider-manifest.json') -Raw | ConvertFrom-Json -Depth 100
Assert-ExactIdentity -Observed $installation.definition -Expected $currentDefinition.identity -Subject 'Installed canonical definition'
Assert-ExactIdentity -Observed $installation.provider.provider -Expected $currentProvider.providerIdentity -Subject 'Installed provider'
Assert-ExactIdentity -Observed $installation.provider.adapter -Expected $currentProvider.adapterIdentity -Subject 'Installed adapter'
Assert-ExactIdentity -Observed $installation.provider.conformanceProfile -Expected $currentProvider.conformanceProfile -Subject 'Installed conformance profile'
Assert-ExactIdentity -Observed $reviewPacket.definition -Expected $installation.definition -Subject 'Packet definition'
Assert-ExactIdentity -Observed $reviewPacket.provider.provider -Expected $installation.provider.provider -Subject 'Packet provider'
Assert-ExactIdentity -Observed $reviewPacket.provider.adapter -Expected $installation.provider.adapter -Subject 'Packet adapter'
Assert-ExactIdentity -Observed $reviewPacket.provider.conformanceProfile -Expected $installation.provider.conformanceProfile -Subject 'Packet conformance profile'

$programKit = Resolve-SeedFile -LogicalPath $programKitLogicalPath
$versionOutput = (& $programKit version --format json 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'The exact workspace-local Program Kit CLI failed its read-only version preflight.' }
$versionResult = $versionOutput | ConvertFrom-Json -Depth 100
if ($versionResult.schema -cne 'program-kit.operation-result/v1' -or
    $versionResult.outcome -cne 'succeeded' -or
    $versionResult.effectState -cne 'none' -or
    $versionResult.primaryDisposition -cne 'complete' -or
    $versionResult.utility.cli -cne $installation.cliRelease.reportedVersion -or
    $installation.cliRelease.executableDigest -cne (Get-ByteDigest -Path $programKit)) {
    throw 'The workspace-local Program Kit CLI does not match the admitted installation record.'
}

[ordered]@{
    schema = 'program-kit.codex-session-review-preflight/v1'
    status = 'ready'
    scenarioIdentity = $seedContract.scenarioIdentity
    seedContractDigest = Get-ByteDigest -Path $contract
    packetDigest = Get-ByteDigest -Path $packet
    cliDigest = Get-ByteDigest -Path $programKit
    projectionDigest = Get-ByteDigest -Path (Resolve-SeedFile '.agents/skills/program-kit/SKILL.md')
    installationRecordDigest = Get-ByteDigest -Path (Resolve-SeedFile '.program-kit/session-integrations/codex/installation.json')
    installationIdentity = $installation.installationIdentity
    definition = $installation.definition
    provider = $installation.provider
    cliRelease = $installation.cliRelease
    constructAuthorityGrant = [ordered]@{
        logicalPath = [string]$construct.authorityGrant.logicalPath
        digest = [string]$construct.authorityGrant.digest
    }
    dependencyMirror = $dependencyMirror
} | ConvertTo-Json -Depth 20 -Compress
