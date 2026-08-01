[CmdletBinding()]
param(
    [ValidateSet('Debug', 'Release')]
    [string] $Configuration = 'Release',

    [Parameter(Mandatory = $true)]
    [string] $OutputPath
)

$ErrorActionPreference = 'Stop'

function ConvertTo-DeterministicNuGetPackage {
    param([string] $Source, [string] $Destination)

    Add-Type -AssemblyName System.IO.Compression
    $pkSourceArchive = [IO.Compression.ZipFile]::OpenRead($Source)
    try {
        $pkEntries = [Collections.Generic.List[object]]::new()
        foreach ($pkEntry in $pkSourceArchive.Entries) {
            if ([string]::IsNullOrEmpty($pkEntry.Name)) { continue }
            $pkStream = $pkEntry.Open()
            $pkBuffer = [IO.MemoryStream]::new()
            try { $pkStream.CopyTo($pkBuffer) }
            finally { $pkStream.Dispose() }
            $pkName = $pkEntry.FullName.Replace('\', '/')
            $pkBytes = $pkBuffer.ToArray()
            $pkBuffer.Dispose()
            if ($pkName -like 'package/services/metadata/core-properties/*.psmdcp') {
                $pkName = 'package/services/metadata/core-properties/program-kit.psmdcp'
            }
            elseif ($pkName -eq '_rels/.rels') {
                $pkRelationships = '<?xml version="1.0" encoding="utf-8"?>' + "`n" +
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "`n" +
                    '  <Relationship Type="http://schemas.microsoft.com/packaging/2010/07/manifest" Target="/Orbyss.ProgramKit.Cli.nuspec" Id="RManifest" />' + "`n" +
                    '  <Relationship Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="/package/services/metadata/core-properties/program-kit.psmdcp" Id="RCore" />' + "`n" +
                    '</Relationships>' + "`n"
                $pkBytes = [Text.Encoding]::UTF8.GetBytes($pkRelationships)
            }
            $pkEntries.Add([pscustomobject]@{ Name = $pkName; Bytes = $pkBytes })
        }
    }
    finally { $pkSourceArchive.Dispose() }

    $pkOutputStream = [IO.File]::Open($Destination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    $pkOutputArchive = [IO.Compression.ZipArchive]::new($pkOutputStream, [IO.Compression.ZipArchiveMode]::Create, $false)
    try {
        foreach ($pkItem in $pkEntries | Sort-Object Name) {
            $pkOutputEntry = $pkOutputArchive.CreateEntry($pkItem.Name, [IO.Compression.CompressionLevel]::Optimal)
            $pkOutputEntry.LastWriteTime = [DateTimeOffset]::new(1980, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
            $pkOutputEntry.ExternalAttributes = 0
            $pkOutputEntryStream = $pkOutputEntry.Open()
            try { $pkOutputEntryStream.Write($pkItem.Bytes, 0, $pkItem.Bytes.Length) }
            finally { $pkOutputEntryStream.Dispose() }
        }
    }
    finally {
        $pkOutputArchive.Dispose()
        $pkOutputStream.Dispose()
    }
}

$pkRepositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$pkRuntimeInputs = @(
    'src',
    'Directory.Build.props',
    'Directory.Build.targets',
    'Directory.Packages.props',
    'global.json',
    'NuGet.Config',
    'ProgramKit.slnx',
    'eng/Pack-ProgramKitTool.ps1'
)
$pkRuntimeStatus = @(& git -C $pkRepositoryRoot status --porcelain -- @pkRuntimeInputs)
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect the runtime source identity.' }
if ($pkRuntimeStatus.Count -ne 0) { throw 'The runtime/build inputs must be committed before a review kit can be sealed.' }
$pkRuntimeCommit = (& git -C $pkRepositoryRoot log -1 --format=%H -- @pkRuntimeInputs | Select-Object -First 1)
if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve the runtime source commit.' }
$pkRuntimeCommit = ([string]$pkRuntimeCommit).Trim()
if ($pkRuntimeCommit -notmatch '^[0-9a-f]{40}$') { throw 'The runtime source commit is not exact.' }
$pkRuntimeSourceRevision = 'git-sha1:' + $pkRuntimeCommit
$pkOutput = [IO.Path]::GetFullPath($OutputPath)
if ($pkOutput -eq $pkRepositoryRoot -or $pkOutput.StartsWith($pkRepositoryRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The external Claude review kit must not be exported inside the Program Kit source repository.'
}
if (Test-Path -LiteralPath $pkOutput) {
    if (@(Get-ChildItem -LiteralPath $pkOutput -Force).Count -gt 0) { throw 'The review-kit output directory must be absent or empty.' }
}
else {
    New-Item -ItemType Directory -Path $pkOutput | Out-Null
}

$pkFeed = Join-Path $pkOutput 'feed'
$pkPackScratch = Join-Path $pkOutput '.pack'
$pkFixtures = Join-Path $pkOutput 'fixtures'
$pkSchemas = Join-Path $pkOutput 'schemas'
$pkScripts = Join-Path $pkOutput 'scripts'
New-Item -ItemType Directory -Path $pkFeed, $pkPackScratch, $pkFixtures, $pkSchemas, $pkScripts -Force | Out-Null

& (Join-Path $PSScriptRoot 'Pack-ProgramKitTool.ps1') -OutputRoot $pkPackScratch -SourceRevisionId $pkRuntimeCommit
if ($LASTEXITCODE -ne 0) { throw 'Program Kit packaging failed.' }
$pkPackages = @(Get-ChildItem -LiteralPath $pkPackScratch -Filter 'Orbyss.ProgramKit.Cli.*.nupkg' -File | Where-Object { $_.Name -notlike '*.snupkg' })
if ($pkPackages.Count -ne 1) { throw 'Exactly one Program Kit CLI package must be produced.' }
$pkPackage = $pkPackages[0]
ConvertTo-DeterministicNuGetPackage -Source $pkPackage.FullName -Destination (Join-Path $pkFeed $pkPackage.Name)
$pkScratchResolved = [IO.Path]::GetFullPath($pkPackScratch)
if (-not $pkScratchResolved.StartsWith($pkOutput + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Refusing review-kit scratch cleanup outside the output root.' }
Remove-Item -LiteralPath $pkScratchResolved -Recurse -Force


Copy-Item -LiteralPath (Join-Path $pkRepositoryRoot 'tests/Fixtures/SessionIntegration/ClaudeCode') -Destination (Join-Path $pkFixtures 'ClaudeCode') -Recurse
Copy-Item -LiteralPath (Join-Path $pkRepositoryRoot 'tests/Fixtures/SessionIntegration/Providers/Conformance') -Destination (Join-Path $pkFixtures 'SharedConformance') -Recurse
Copy-Item -LiteralPath (Join-Path $pkRepositoryRoot 'src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Schemas/isolated-machine-review.schema.json') -Destination (Join-Path $pkSchemas 'isolated-machine-review.schema.json')
Copy-Item -LiteralPath (Join-Path $pkRepositoryRoot 'src/ProgramKit.Contracts/Schemas/common.schema.json') -Destination (Join-Path $pkSchemas 'common.schema.json')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ClaudeCodeReview/Initialize-ConsumerWorkspace.ps1') -Destination $pkScripts
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ClaudeCodeReview/Invoke-DeterministicConsumerProof.ps1') -Destination $pkScripts
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ClaudeCodeReview/Invoke-ClaudeCodeTrials.ps1') -Destination $pkScripts
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ClaudeCodeReview/Complete-HumanReview.ps1') -Destination $pkScripts
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'ClaudeCodeReview/README.md') -Destination (Join-Path $pkOutput 'README.md')

$pkFiles = @(Get-ChildItem -LiteralPath $pkOutput -Recurse -File | Where-Object { $_.Name -ne 'manifest.json' } | ForEach-Object {
    $pkRelative = [IO.Path]::GetRelativePath($pkOutput, $_.FullName).Replace('\', '/')
    [ordered]@{
        logicalPath = $pkRelative
        digest = 'sha256:' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        length = $_.Length
    }
} | Sort-Object { $_.logicalPath })
$pkCliPackageFiles = @($pkFiles | Where-Object logicalPath -Like 'feed/Orbyss.ProgramKit.Cli.*.nupkg')
$pkReviewSchemaFiles = @($pkFiles | Where-Object logicalPath -EQ 'schemas/isolated-machine-review.schema.json')
$pkCommonSchemaFiles = @($pkFiles | Where-Object logicalPath -EQ 'schemas/common.schema.json')
$pkCorpusFiles = @($pkFiles | Where-Object logicalPath -Like 'fixtures/SharedConformance/*')
if ($pkCliPackageFiles.Count -ne 1 -or $pkReviewSchemaFiles.Count -ne 1 -or $pkCommonSchemaFiles.Count -ne 1 -or $pkCorpusFiles.Count -eq 0) {
    throw 'The sealed review-kit component closure is incomplete.'
}
$pkProviderManifest = Get-Content -Raw -LiteralPath (Join-Path $pkRepositoryRoot 'src/ProgramKit.SessionIntegration.Providers.ClaudeCode/Manifest/claude-code-provider-manifest.json') | ConvertFrom-Json -Depth 20
$pkCorpusIdentityInput = ($pkCorpusFiles | ForEach-Object { [IO.Path]::GetFileName($_.logicalPath) + ':' + $_.digest }) -join "`n"
$pkCorpusIdentityBytes = [Text.Encoding]::UTF8.GetBytes($pkCorpusIdentityInput)
$pkCorpusDigest = 'sha256:' + [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($pkCorpusIdentityBytes)).ToLowerInvariant()
$pkComponentBindings = [ordered]@{
    cliPackageDigest = $pkCliPackageFiles[0].digest
    providerDigest = $pkProviderManifest.providerIdentity.digest
    adapterDigest = $pkProviderManifest.adapterIdentity.digest
    definitionDigest = $pkProviderManifest.definitionBinding.digest
    diagnosticCatalogDigest = $pkProviderManifest.diagnosticCatalog.digest
    conformanceProfileDigest = $pkProviderManifest.conformanceProfile.digest
    conformanceCorpusDigest = $pkCorpusDigest
    machineReviewSchemaDigest = $pkReviewSchemaFiles[0].digest
    commonSchemaDigest = $pkCommonSchemaFiles[0].digest
}
$pkIdentityLines = [Collections.Generic.List[string]]::new()
foreach ($pkFile in $pkFiles) { $pkIdentityLines.Add($pkFile.logicalPath + ':' + $pkFile.digest + ':' + $pkFile.length) }
$pkIdentityLines.Add('runtime-source:' + $pkRuntimeSourceRevision)
foreach ($pkBinding in $pkComponentBindings.GetEnumerator()) { $pkIdentityLines.Add('binding:' + $pkBinding.Key + ':' + $pkBinding.Value) }
$pkIdentityInput = $pkIdentityLines -join "`n"
$pkIdentityBytes = [Text.Encoding]::UTF8.GetBytes($pkIdentityInput)
$pkHasher = [Security.Cryptography.SHA256]::Create()
try { $pkKitDigest = 'sha256:' + [Convert]::ToHexString($pkHasher.ComputeHash($pkIdentityBytes)).ToLowerInvariant() }
finally { $pkHasher.Dispose() }

$pkManifest = [ordered]@{
    schema = 'program-kit.claude-code-review-kit/v1'
    canonicalProfile = 'program-kit.canonical-json/v1'
    reviewKitDigest = $pkKitDigest
    runtimeSourceRevision = $pkRuntimeSourceRevision
    cliPackage = 'Orbyss.ProgramKit.Cli@1.0.0-alpha.1'
    definition = 'orbyss.program-kit:session-integration-definition:human-led-software-factory@1.0.0'
    provider = 'anthropic:session-provider:claude-code@2.1.220'
    adapter = 'orbyss.program-kit:session-provider-adapter:claude-code-project-skill@1.0.0'
    diagnosticCatalog = 'orbyss.program-kit.claude-code:diagnostic-catalog:session-provider@1.0.0'
    conformanceProfile = 'orbyss.program-kit:session-provider-conformance:repository-skill-v1@1.0.0'
    componentBindings = $pkComponentBindings
    supportClaim = 'not-evaluated'
    canonicalDependencyStatus = 'rejected'
    limitations = @('feature-002-product-acceptance-rejected', 'live-claude-review-not-executed')
    files = $pkFiles
}
$pkManifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $pkOutput 'manifest.json') -Encoding utf8NoBOM
Write-Output ($pkManifest | ConvertTo-Json -Depth 10 -Compress)
