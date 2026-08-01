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
if ($pkManifest.canonicalProfile -ne 'program-kit.canonical-json/v1') { throw 'The review-kit canonical profile is unsupported.' }
if ($pkManifest.provider -ne 'anthropic:session-provider:claude-code@2.1.220') { throw 'The sealed provider selection is not exact.' }
if ($pkManifest.adapter -ne 'orbyss.program-kit:session-provider-adapter:claude-code-project-skill@1.0.0') { throw 'The sealed adapter selection is not exact.' }
if ($pkManifest.supportClaim -ne 'not-evaluated' -or $pkManifest.canonicalDependencyStatus -ne 'rejected') { throw 'This kit is not the expected fail-closed Feature 003 review state.' }

$pkLogicalPaths = @($pkManifest.files | ForEach-Object { [string]$_.logicalPath })
if ($pkLogicalPaths.Count -eq 0 -or @($pkLogicalPaths | Sort-Object -Unique).Count -ne $pkLogicalPaths.Count) { throw 'The review-kit file inventory is empty or ambiguous.' }
if ((Compare-Object $pkLogicalPaths @($pkLogicalPaths | Sort-Object) -SyncWindow 0).Count -ne 0) { throw 'The review-kit file inventory is not canonically ordered.' }
foreach ($pkFile in $pkManifest.files) {
    $pkPath = [IO.Path]::GetFullPath((Join-Path $pkKit $pkFile.logicalPath))
    if (-not $pkPath.StartsWith($pkKit + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'A review-kit path escapes the sealed root.' }
    if (-not (Test-Path -LiteralPath $pkPath -PathType Leaf)) { throw "Missing sealed review-kit file: $($pkFile.logicalPath)" }
    $pkDigest = 'sha256:' + (Get-FileHash -LiteralPath $pkPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($pkDigest -ne $pkFile.digest) { throw "Review-kit digest mismatch: $($pkFile.logicalPath)" }
    if ((Get-Item -LiteralPath $pkPath).Length -ne $pkFile.length) { throw "Review-kit length mismatch: $($pkFile.logicalPath)" }
}

$pkBindingNames = @(
    'cliPackageDigest',
    'providerDigest',
    'adapterDigest',
    'definitionDigest',
    'diagnosticCatalogDigest',
    'conformanceProfileDigest',
    'conformanceCorpusDigest',
    'machineReviewSchemaDigest',
    'commonSchemaDigest'
)
$pkObservedBindingNames = @($pkManifest.componentBindings.PSObject.Properties.Name)
if (@(Compare-Object $pkBindingNames $pkObservedBindingNames).Count -ne 0) { throw 'The review-kit component binding set is incomplete or unknown.' }
$pkIdentityLines = [Collections.Generic.List[string]]::new()
foreach ($pkFile in $pkManifest.files) { $pkIdentityLines.Add($pkFile.logicalPath + ':' + $pkFile.digest + ':' + $pkFile.length) }
foreach ($pkBindingName in $pkBindingNames) {
    $pkBindingValue = [string]$pkManifest.componentBindings.$pkBindingName
    if ($pkBindingValue -notmatch '^sha256:[0-9a-f]{64}$') { throw "Invalid component digest: $pkBindingName" }
    $pkIdentityLines.Add('binding:' + $pkBindingName + ':' + $pkBindingValue)
}
$pkIdentityBytes = [Text.Encoding]::UTF8.GetBytes($pkIdentityLines -join ([char]10))
$pkObservedKitDigest = 'sha256:' + [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($pkIdentityBytes)).ToLowerInvariant()
if ($pkObservedKitDigest -ne $pkManifest.reviewKitDigest) { throw 'The aggregate review-kit identity does not match its sealed files and component bindings.' }

$pkCliFiles = @($pkManifest.files | Where-Object logicalPath -Like 'feed/Orbyss.ProgramKit.Cli.*.nupkg')
$pkReviewSchemas = @($pkManifest.files | Where-Object logicalPath -EQ 'schemas/isolated-machine-review.schema.json')
$pkCommonSchemas = @($pkManifest.files | Where-Object logicalPath -EQ 'schemas/common.schema.json')
$pkCorpusFiles = @($pkManifest.files | Where-Object logicalPath -Like 'fixtures/SharedConformance/*')
if ($pkCliFiles.Count -ne 1 -or $pkReviewSchemas.Count -ne 1 -or $pkCommonSchemas.Count -ne 1 -or $pkCorpusFiles.Count -eq 0) { throw 'The sealed component file closure is incomplete.' }
if ($pkCliFiles[0].digest -ne $pkManifest.componentBindings.cliPackageDigest) { throw 'The CLI package binding is inconsistent.' }
if ($pkReviewSchemas[0].digest -ne $pkManifest.componentBindings.machineReviewSchemaDigest) { throw 'The machine-review schema binding is inconsistent.' }
if ($pkCommonSchemas[0].digest -ne $pkManifest.componentBindings.commonSchemaDigest) { throw 'The common schema binding is inconsistent.' }
$pkCorpusInput = ($pkCorpusFiles | ForEach-Object { [IO.Path]::GetFileName($_.logicalPath) + ':' + $_.digest }) -join ([char]10)
$pkCorpusDigest = 'sha256:' + [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($pkCorpusInput))).ToLowerInvariant()
if ($pkCorpusDigest -ne $pkManifest.componentBindings.conformanceCorpusDigest) { throw 'The shared conformance corpus binding is inconsistent.' }

$pkOsFamily = if ($IsWindows) { 'windows' } elseif ($IsLinux) { 'linux' } else { throw 'The isolated review OS is unsupported.' }
$pkDotnetVersion = (& dotnet --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $pkDotnetVersion -ne '10.0.302') { throw 'The isolated review requires exact .NET SDK 10.0.302.' }

$pkConsumer = [IO.Path]::GetFullPath($ConsumerRoot)
$pkContaminants = @('.program-kit-source.json', '.specify', '.agents/skills/program-kit', '.claude/skills/program-kit', '.program-kit/session-integrations')
foreach ($pkRelative in $pkContaminants) {
    if (Test-Path -LiteralPath (Join-Path $pkConsumer $pkRelative)) { throw "Isolated boundary contamination: $pkRelative" }
}
if (Test-Path -LiteralPath $pkConsumer) {
    if (@(Get-ChildItem -LiteralPath $pkConsumer -Force).Count -gt 0) { throw 'The isolated consumer root must be absent or empty.' }
}
else { New-Item -ItemType Directory -Path $pkConsumer | Out-Null }

git -C $pkConsumer init --quiet
if ($LASTEXITCODE -ne 0) { throw 'Could not initialize the isolated consumer repository.' }

$pkEnvironment = [ordered]@{
    schema = 'program-kit.claude-code-environment/v1'
    osFamily = $pkOsFamily
    osArchitecture = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    dotnetSdk = $pkDotnetVersion
    workspaceProfile = 'fresh-empty-git-repository'
    cleanBoundaryPassed = $true
    sourceAbsent = $true
    specKitAbsent = $true
    codexProjectionAbsent = $true
    claudeProjectionAbsent = $true
    priorSessionStateAbsent = $true
    reviewKitDigest = $pkManifest.reviewKitDigest
    cliPackageDigest = $pkManifest.componentBindings.cliPackageDigest
    selectedProviderVersion = '2.1.220'
    supportClaim = $pkManifest.supportClaim
    canonicalDependencyStatus = $pkManifest.canonicalDependencyStatus
}
$pkEnvironment | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $pkConsumer 'environment.json') -Encoding utf8NoBOM
Write-Output ($pkEnvironment | ConvertTo-Json -Depth 10 -Compress)
