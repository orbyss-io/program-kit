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
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Missing artifact: $path"
    $actual = Get-LfDigest $path
    Assert-True ($actual -eq $expected) "Digest mismatch: $path ($actual)"
}

function Read-Json([string] $path) {
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -Depth 100
}

function Get-ComparableJson([object] $value, [string[]] $excludedProperties) {
    $result = [ordered]@{}
    foreach ($property in $value.PSObject.Properties) {
        if ($excludedProperties -notcontains $property.Name) {
            $result[$property.Name] = $property.Value
        }
    }
    return $result | ConvertTo-Json -Depth 100 -Compress
}

function Assert-Reference(
    [object] $value,
    [string] $identity,
    [string] $version,
    [string] $digest,
    [string] $label
) {
    Assert-True ($null -ne $value) "$label is missing."
    Assert-True ($value.identity -eq $identity) "$label identity differs."
    Assert-True ($value.version -eq $version) "$label version differs."
    Assert-True ($value.digest -eq "sha256:$digest") "$label digest differs."
}

$baseDesignPath = Join-Path $reviewSetRoot 'architecture-design.json'
$basePlanPath = Join-Path $reviewSetRoot 'implementation-plan.json'
$baseDispositionPath = Join-Path $reviewSetRoot 'static-conformance-disposition.json'
$baseApprovalPath = Join-Path $reviewSetRoot 'design-plan-approval.json'
Assert-Digest $baseDesignPath $baseDesignDigest
Assert-Digest $basePlanPath $basePlanDigest
Assert-Digest $baseDispositionPath $baseDispositionDigest
Assert-Digest $baseApprovalPath $baseApprovalDigest
Assert-Digest (Join-Path $repositoryRoot 'Directory.Build.targets') $matrixDigest
Assert-Digest (Join-Path $repositoryRoot 'build\Invoke-CSharpGateTestPlan.ps1') $currentProfileDigest

$basePlan = Read-Json $basePlanPath
$baseDesign = Read-Json $baseDesignPath
$baseDisposition = Read-Json $baseDispositionPath
$approval = Read-Json $baseApprovalPath
$manifest = Read-Json (Join-Path $amendmentRoot 'review-manifest.json')
$design = Read-Json (Join-Path $amendmentRoot 'architecture-design.json')
$disposition = Read-Json (Join-Path $amendmentRoot 'static-conformance-disposition.json')
$policy = Read-Json (Join-Path $amendmentRoot 'verification-profile-compatibility-policy.json')
$plan = Read-Json (Join-Path $amendmentRoot 'implementation-plan.json')

Assert-True ($approval.decision -eq 'approved') 'The frozen approval is not approved.'
Assert-True ($approval.supersession.state -eq 'active') 'The frozen approval is not active.'
Assert-True ($manifest.sourceCommit -eq $baseCommit) 'The amendment source commit differs.'
Assert-True ($manifest.state -eq 'ready-for-human-decision') 'The amendment state differs.'
Assert-True ($manifest.approvalBoundary.implementationMayStart -eq $false) 'The amendment grants implementation authority.'
Assert-True ($manifest.approvalBoundary.decision -eq 'awaiting-exact-human-approval') 'The approval boundary differs.'

Assert-True ($design.'$schema' -eq 'https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.3/architecture-design.schema.json') 'The design schema differs.'
Assert-True ($disposition.'$schema' -eq 'https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.2/static-conformance-disposition.schema.json') 'The disposition schema differs.'
Assert-True ($plan.'$schema' -eq 'https://schemas.orbyss.io/program-kit/planning/implementation-plan/0.1.0-alpha.5/schema.json') 'The plan schema differs.'

Assert-True `
    ((Get-ComparableJson $design @('$schema', 'staticConformanceDisposition')) -eq
        (Get-ComparableJson $baseDesign @('staticConformanceDisposition'))) `
    'The current design changes an approved semantic field.'
Assert-True `
    ((Get-ComparableJson $disposition @('$schema', 'softwareDesign')) -eq
        (Get-ComparableJson $baseDisposition @('softwareDesign'))) `
    'The current disposition changes an approved decision field.'

$designDigest = Get-LfDigest (Join-Path $amendmentRoot 'architecture-design.json')
$dispositionDigest = Get-LfDigest (Join-Path $amendmentRoot 'static-conformance-disposition.json')
$policyDigest = Get-LfDigest (Join-Path $amendmentRoot 'verification-profile-compatibility-policy.json')
$planDigest = Get-LfDigest (Join-Path $amendmentRoot 'implementation-plan.json')
Assert-Reference $plan.design 'pkid:design:program-kit:development-tools' '0.1.0-alpha.3' $designDigest 'Plan design'
Assert-Reference $plan.staticConformanceDisposition 'pkid:static-conformance-disposition:program-kit:development-tools' '0.1.0-alpha.2' $dispositionDigest 'Plan disposition'
Assert-True ($plan.staticConformanceState -eq 'reuse-existing') 'The static-conformance state changed.'

Assert-True `
    ((Get-ComparableJson $plan @('$schema', 'design', 'workUnits', 'staticConformanceDisposition')) -eq
        (Get-ComparableJson $basePlan @('design', 'workUnits', 'staticConformanceDisposition'))) `
    'The alpha.5 plan changes a non-binding approved plan field.'
Assert-True ($plan.workUnits.Count -eq $basePlan.workUnits.Count) 'Work-unit count changed.'

for ($index = 0; $index -lt $basePlan.workUnits.Count; $index++) {
    $baseUnit = $basePlan.workUnits[$index]
    $unit = $plan.workUnits[$index]
    Assert-True `
        ((Get-ComparableJson $unit @('activationMatrix', 'verificationProfile')) -eq
            (Get-ComparableJson $baseUnit @('activationMatrix', 'verificationProfile'))) `
        "Approved work-unit semantics changed: $($baseUnit.workUnitId)"
    Assert-True ($unit.activationMatrix.resolutionMode -eq 'approval-fixed') "Activation mode differs: $($baseUnit.workUnitId)"
    Assert-True ($null -eq $unit.activationMatrix.approvedIdentity) "Fixed activation identity must be null: $($baseUnit.workUnitId)"
    Assert-True ($null -eq $unit.activationMatrix.acceptedVersions) "Fixed activation range must be null: $($baseUnit.workUnitId)"
    Assert-True ($null -eq $unit.activationMatrix.compatibilityPolicy) "Fixed activation policy must be null: $($baseUnit.workUnitId)"
    Assert-True `
        (($unit.activationMatrix.approvedArtifact | ConvertTo-Json -Depth 20 -Compress) -eq
            ($baseUnit.activationMatrix | ConvertTo-Json -Depth 20 -Compress)) `
        "Fixed activation artifact changed: $($baseUnit.workUnitId)"
    Assert-True ($unit.verificationProfile.resolutionMode -eq 'execution-resolved') "Profile mode differs: $($baseUnit.workUnitId)"
    Assert-True ($null -eq $unit.verificationProfile.approvedArtifact) "Resolved profile exact artifact must be null: $($baseUnit.workUnitId)"
    Assert-True ($unit.verificationProfile.approvedIdentity -eq $baseUnit.verificationProfile.identity) "Resolved profile identity changed: $($baseUnit.workUnitId)"
    Assert-True ($unit.verificationProfile.acceptedVersions -eq $acceptedProfileVersions) "Resolved profile range changed: $($baseUnit.workUnitId)"
    Assert-Reference `
        $unit.verificationProfile.compatibilityPolicy `
        $policy.identity `
        $policy.version `
        $policyDigest `
        "Profile policy for $($baseUnit.workUnitId)"
}

Assert-True ($policy.sourceCommit -eq $baseCommit) 'Compatibility-policy source commit differs.'
Assert-True ($policy.approvedIdentity -eq 'pkid:profile:program-kit:private-csharp-gate-exhaustive') 'Compatibility-policy identity differs.'
Assert-True ($policy.acceptedVersions -eq $acceptedProfileVersions) 'Compatibility-policy range differs.'
Assert-Reference $policy.approvedBaseline $policy.approvedIdentity '1.0.0' '80978c4209e5119c8df468f47f972ea8dc622bbeb907681e48721d5d8f12738d' 'Approved profile baseline'
Assert-Reference $policy.currentCompatibleSelection $policy.approvedIdentity '1.0.1' $currentProfileDigest 'Current compatible profile'

$closure = @($plan.workUnits | Where-Object { $_.workUnitKind -eq 'closure' })
Assert-True ($closure.Count -eq 1) 'The plan must retain exactly one closure work unit.'
Assert-True ($closure[0].workUnitId -eq 'PKDT-W110') 'The closure work unit changed.'

foreach ($artifact in $manifest.artifacts) {
    $artifactPath = Join-Path $amendmentRoot $artifact.path
    Assert-Digest $artifactPath $artifact.sha256.Substring(7)
}
$requiredDigests = @($manifest.approvalBoundary.requiredArtifactDigests)
Assert-True ($requiredDigests.Count -eq 4) 'The exact approval set must contain four artifacts.'
foreach ($required in @("sha256:$designDigest", "sha256:$dispositionDigest", "sha256:$policyDigest", "sha256:$planDigest")) {
    Assert-True ($requiredDigests -contains $required) "Approval set omits $required"
}

$projection = Get-Content -LiteralPath (Join-Path $amendmentRoot 'implementation-plan.md') -Raw
Assert-True ($projection.Contains('Non-authoritative human-readable projection', [StringComparison]::Ordinal)) 'The plan projection is not labelled non-authoritative.'
Assert-True ($projection.Contains("sha256:$planDigest", [StringComparison]::Ordinal)) 'The plan projection digest is stale.'
Assert-True ($projection.Contains('implementation remains `not-started`', [StringComparison]::Ordinal)) 'The plan projection overstates implementation.'

Push-Location $repositoryRoot
try {
    & git cat-file -e "$baseCommit`^{commit}"
    Assert-True ($LASTEXITCODE -eq 0) 'The exact source commit is unavailable.'
    & git diff --check
    Assert-True ($LASTEXITCODE -eq 0) 'git diff --check failed.'
} finally {
    Pop-Location
}

Write-Output "Development Tools alpha.5 execution-binding amendment validation passed: sha256:$planDigest"
