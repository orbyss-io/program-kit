[CmdletBinding()]
param(
    [switch]$InitializeSelection
)

$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$selectionPath = Join-Path $PSScriptRoot 'active-owned-schema-migration-selection.json'
$migrationRoot = Join-Path $PSScriptRoot 'migrations\active-owned-schemas'
$fixturePath = Join-Path $PSScriptRoot 'migrations\fixtures\active-owned-schema-alpha-rewrite.fixture.json'
$designDigest = 'sha256:2b8027d505dfcef7f1b28bc3aecf3333b575e59928dabb7121d24f28be2811ba'

function Get-RelativePath([string]$path) {
    return [IO.Path]::GetRelativePath($repoRoot, $path).Replace('\', '/')
}

function Get-Digest([string]$path) {
    return 'sha256:' + (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Write-CanonicalJson([string]$path, [object]$value) {
    $parent = Split-Path -Parent $path
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }

    $text = $value | ConvertTo-Json -Depth 100
    $text = $text.Replace(
        "`r`n",
        "`n",
        [StringComparison]::Ordinal).Replace(
            "`r",
            "`n",
            [StringComparison]::Ordinal) + "`n"
    [IO.File]::WriteAllText($path, $text, [Text.UTF8Encoding]::new($false))
}

function Get-TargetPath([string]$sourcePath, [string]$targetVersion) {
    if ($sourcePath -match '^(.*)-\d+\.\d+\.\d+\.schema\.json$') {
        return $Matches[1] + '-' + $targetVersion + '.schema.json'
    }

    if ($sourcePath.EndsWith('.schema.json', [StringComparison]::Ordinal)) {
        return $sourcePath.Substring(0, $sourcePath.Length - '.schema.json'.Length) +
            '-' + $targetVersion + '.schema.json'
    }

    throw "Unsupported schema path: $sourcePath"
}

function Initialize-Selection {
    if (Test-Path -LiteralPath $selectionPath) {
        throw "Selection already exists: $selectionPath"
    }

    $candidates = @()
    Get-ChildItem -LiteralPath (Join-Path $repoRoot 'schemas') -Recurse -Filter '*.schema.json' |
        Where-Object { $_.FullName -notmatch '[\\/]vendor[\\/]' } |
        ForEach-Object {
            try {
                $document = Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json
            }
            catch {
                return
            }

            $identity = $document.'x-program-kit-identity'
            $version = $document.'x-program-kit-version'
            $canonicalId = $document.'$id'
            if ($identity -and
                $identity.StartsWith('pkid:schema:program-kit:', [StringComparison]::Ordinal) -and
                $version -and
                $canonicalId) {
                $candidates += [pscustomobject]@{
                    identity = $identity
                    version = $version
                    canonicalId = $canonicalId
                    fullPath = $_.FullName
                    sourcePath = Get-RelativePath $_.FullName
                }
            }
        }

    $entries = @()
    foreach ($group in ($candidates | Group-Object identity | Sort-Object Name)) {
        if ($group.Group | Where-Object { $_.version -match '^0\.1\.0-alpha\.[1-9][0-9]*$' }) {
            continue
        }

        $source = $group.Group |
            Sort-Object { [Version]$_.version } -Descending |
            Select-Object -First 1
        $sourceVersion = [Version]$source.version
        $ordinal = $sourceVersion.Major
        if ($ordinal -le 0) {
            throw "Cannot derive a positive reviewed ordinal for $($source.identity)@$($source.version)."
        }

        $targetVersion = "0.1.0-alpha.$ordinal"
        $targetPath = Get-TargetPath $source.sourcePath $targetVersion
        $targetCanonicalId = $source.canonicalId.Replace(
            "/$($source.version)/",
            "/$targetVersion/",
            [StringComparison]::Ordinal)
        if ($targetCanonicalId -eq $source.canonicalId) {
            throw "Canonical schema ID does not expose its source version: $($source.canonicalId)"
        }

        $entries += [ordered]@{
            identity = $source.identity
            ownerId = 'pkid:domain:program-kit:version-governance'
            sourcePath = $source.sourcePath
            sourceVersion = $source.version
            sourceDigest = Get-Digest $source.fullPath
            sourceCanonicalId = $source.canonicalId
            ownedRevisionOrdinal = $ordinal
            targetPath = $targetPath
            targetVersion = $targetVersion
            targetCanonicalId = $targetCanonicalId
        }
    }

    Write-CanonicalJson $selectionPath ([ordered]@{
        identity = 'pkid:selection:program-kit:active-owned-schema-alpha-transition'
        version = '0.1.0-alpha.1'
        entries = $entries
    })
}

function Rewrite-Reference(
    [string]$reference,
    [object]$current,
    [object[]]$entries) {
    foreach ($entry in $entries) {
        if ($reference.StartsWith(
                $entry.sourceCanonicalId,
                [StringComparison]::Ordinal)) {
            return $entry.targetCanonicalId +
                $reference.Substring($entry.sourceCanonicalId.Length)
        }
    }

    $sourceDirectory = Split-Path -Parent $current.sourcePath
    foreach ($entry in $entries) {
        if ((Split-Path -Parent $entry.sourcePath) -ne $sourceDirectory) {
            continue
        }

        $sourceName = Split-Path -Leaf $entry.sourcePath
        if ($reference.StartsWith($sourceName, [StringComparison]::Ordinal)) {
            return (Split-Path -Leaf $entry.targetPath) +
                $reference.Substring($sourceName.Length)
        }
    }

    return $reference
}

function Rewrite-References([object]$node, [object]$current, [object[]]$entries) {
    if ($null -eq $node) {
        return
    }

    if ($node -is [Collections.IList]) {
        foreach ($item in $node) {
            Rewrite-References $item $current $entries
        }
        return
    }

    if ($node -isnot [pscustomobject]) {
        return
    }

    foreach ($property in @($node.PSObject.Properties)) {
        if ($property.Name -eq '$ref' -and $property.Value -is [string]) {
            $property.Value = Rewrite-Reference $property.Value $current $entries
        }
        else {
            Rewrite-References $property.Value $current $entries
        }
    }
}

function Set-RootConstIfExact(
    [object]$document,
    [string]$propertyName,
    [string]$sourceVersion,
    [string]$targetVersion) {
    if ($null -eq $document.properties) {
        return
    }

    $property = $document.properties.PSObject.Properties[$propertyName]
    if ($null -ne $property -and
        $property.Value.const -eq $sourceVersion) {
        $property.Value.const = $targetVersion
    }
}

function Materialize-Targets([object[]]$entries) {
    foreach ($entry in $entries) {
        $sourcePath = Join-Path $repoRoot $entry.sourcePath
        if ((Get-Digest $sourcePath) -ne $entry.sourceDigest) {
            throw "Legacy source digest changed: $($entry.sourcePath)"
        }

        $document = Get-Content -Raw -LiteralPath $sourcePath | ConvertFrom-Json
        if ($document.'x-program-kit-identity' -ne $entry.identity -or
            $document.'x-program-kit-version' -ne $entry.sourceVersion -or
            $document.'$id' -ne $entry.sourceCanonicalId) {
            throw "Selection no longer matches the exact legacy schema: $($entry.sourcePath)"
        }

        $document.'$id' = $entry.targetCanonicalId
        $document.'x-program-kit-version' = $entry.targetVersion
        Set-RootConstIfExact $document 'version' $entry.sourceVersion $entry.targetVersion
        Set-RootConstIfExact $document 'schemaVersion' $entry.sourceVersion $entry.targetVersion
        Set-RootConstIfExact $document 'manifestVersion' $entry.sourceVersion $entry.targetVersion
        Rewrite-References $document $entry $entries
        Write-CanonicalJson (Join-Path $repoRoot $entry.targetPath) $document
    }
}

function New-Reference(
    [string]$identity,
    [string]$version,
    [string]$digest) {
    return [ordered]@{
        identity = $identity
        version = $version
        digest = $digest
    }
}

function Materialize-MigrationsAndMap([object[]]$entries) {
    $fixtureDigest = Get-Digest $fixturePath
    $implementationDigest = Get-Digest $PSCommandPath
    $evidence = New-Reference `
        'pkid:design:program-kit:alpha-version-transition' `
        '0.1.0-alpha.1' `
        $designDigest
    $nodes = @()
    $edges = @()

    foreach ($entry in $entries) {
        $sourceReference = New-Reference `
            $entry.identity `
            $entry.sourceVersion `
            $entry.sourceDigest
        $targetDigest = Get-Digest (Join-Path $repoRoot $entry.targetPath)
        $targetReference = New-Reference `
            $entry.identity `
            $entry.targetVersion `
            $targetDigest
        $suffix = $entry.identity.Substring('pkid:schema:program-kit:'.Length)
        $migrationIdentity = "pkid:migration:program-kit:$suffix-to-alpha-$($entry.ownedRevisionOrdinal)"
        $migrationPath = Join-Path $migrationRoot "$suffix-to-alpha-$($entry.ownedRevisionOrdinal).migration.json"
        $migration = [ordered]@{
            sourceIdentity = $entry.identity
            sourceRange = "[$($entry.sourceVersion)]"
            target = $targetReference
            mode = 'artifact-transform'
            preconditions = @(
                [ordered]@{
                    code = 'exact-legacy-source'
                    description = 'The source identity, version, and complete-file digest must match the reviewed selection before transformation.'
                    evidenceReferences = @($evidence)
                })
            lossPolicy = 'lossless'
            isDeterministic = $true
            isIdempotent = $true
            failurePolicy = 'preserve-source-and-report'
            implementationReference = New-Reference `
                'pkid:tool:program-kit:active-owned-alpha-materializer' `
                '0.1.0-alpha.1' `
                $implementationDigest
            fixtureReferences = @(
                (New-Reference `
                    'pkid:fixture:program-kit:active-owned-schema-alpha-rewrite' `
                    '0.1.0-alpha.1' `
                    $fixtureDigest))
        }
        Write-CanonicalJson $migrationPath $migration

        $nodes += [ordered]@{
            revision = $sourceReference
            kind = 'schema'
            ownerId = $entry.ownerId
            evidenceReferences = @($evidence)
        }
        $nodes += [ordered]@{
            revision = $targetReference
            kind = 'schema'
            ownerId = $entry.ownerId
            evidenceReferences = @($evidence)
        }
        $edges += [ordered]@{
            id = "pkid:edge:program-kit:$suffix-alpha-$($entry.ownedRevisionOrdinal)-migrates-legacy"
            source = $targetReference
            targetIdentity = $entry.identity
            kind = 'migrates'
            acceptedRange = "[$($entry.sourceVersion)]"
            resolution = $sourceReference
            exposure = 'public'
            compatibilityDimensions = @('wire-read', 'wire-write')
            evidenceReferences = @(
                (New-Reference $migrationIdentity '0.1.0-alpha.1' (Get-Digest $migrationPath)))
        }
    }

    $policySourcePath = Join-Path $repoRoot 'governance\csharp-source-quality-gate.md'
    $policyTargetPath = Join-Path $repoRoot 'governance\csharp-source-quality-gate-0.1.0-alpha.10.md'
    $policyFixturePath = Join-Path $PSScriptRoot 'migrations\fixtures\csharp-source-quality-gate-v1-10-to-alpha10.fixture.json'
    $policyIdentity = 'pkid:policy:program-kit:csharp-source-quality-gate'
    $policySourceReference = New-Reference `
        $policyIdentity `
        '1.10.0' `
        (Get-Digest $policySourcePath)
    $policyTargetReference = New-Reference `
        $policyIdentity `
        '0.1.0-alpha.10' `
        (Get-Digest $policyTargetPath)
    $policyMigrationPath = Join-Path $PSScriptRoot 'migrations\csharp-source-quality-gate-v1-10-to-alpha10.migration.json'
    $policyMigration = [ordered]@{
        sourceIdentity = $policyIdentity
        sourceRange = '[1.10.0]'
        target = $policyTargetReference
        mode = 'artifact-transform'
        preconditions = @(
            [ordered]@{
                code = 'exact-policy-source'
                description = 'The legacy policy bytes and its single version marker must match the approved 1.10.0 revision.'
                evidenceReferences = @($evidence)
            })
        lossPolicy = 'lossless'
        isDeterministic = $true
        isIdempotent = $true
        failurePolicy = 'preserve-source-and-report'
        implementationReference = New-Reference `
            'pkid:tool:program-kit:active-owned-alpha-materializer' `
            '0.1.0-alpha.1' `
            $implementationDigest
        fixtureReferences = @(
            (New-Reference `
                'pkid:fixture:program-kit:csharp-source-quality-gate-v1-10-to-alpha10' `
                '0.1.0-alpha.1' `
                (Get-Digest $policyFixturePath)))
    }
    Write-CanonicalJson $policyMigrationPath $policyMigration
    $nodes += [ordered]@{
        revision = $policySourceReference
        kind = 'artifact'
        ownerId = 'pkid:domain:program-kit:version-governance'
        evidenceReferences = @($evidence)
    }
    $nodes += [ordered]@{
        revision = $policyTargetReference
        kind = 'artifact'
        ownerId = 'pkid:domain:program-kit:version-governance'
        evidenceReferences = @($evidence)
    }
    $edges += [ordered]@{
        id = 'pkid:edge:program-kit:csharp-source-quality-gate-alpha-10-migrates-v1-10'
        source = $policyTargetReference
        targetIdentity = $policyIdentity
        kind = 'migrates'
        acceptedRange = '[1.10.0]'
        resolution = $policySourceReference
        exposure = 'private'
        compatibilityDimensions = @('semantic-behavior', 'source-api')
        evidenceReferences = @(
            (New-Reference `
                'pkid:migration:program-kit:csharp-source-quality-gate-v1-10-to-alpha10' `
                '0.1.0-alpha.1' `
                (Get-Digest $policyMigrationPath)))
    }

    Write-CanonicalJson (Join-Path $PSScriptRoot 'active-owned-alpha-transition-map.json') ([ordered]@{
        nodes = $nodes
        edges = $edges
    })
}

function Materialize-CSharpPolicy {
    $sourcePath = Join-Path $repoRoot 'governance\csharp-source-quality-gate.md'
    $targetPath = Join-Path $repoRoot 'governance\csharp-source-quality-gate-0.1.0-alpha.10.md'
    $sourceText = [IO.File]::ReadAllText($sourcePath)
    $sourceMarker = 'Policy version: `1.10.0`'
    if (($sourceText.Split($sourceMarker).Length - 1) -ne 1) {
        throw 'The C# policy source must contain exactly one reviewed legacy version marker.'
    }

    $targetText = $sourceText.Replace(
        $sourceMarker,
        'Policy version: `0.1.0-alpha.10`',
        [StringComparison]::Ordinal)
    [IO.File]::WriteAllText(
        $targetPath,
        $targetText,
        [Text.UTF8Encoding]::new($false))
}

if ($InitializeSelection) {
    Initialize-Selection
}

if (-not (Test-Path -LiteralPath $selectionPath)) {
    throw "Missing reviewed selection: $selectionPath"
}

$selection = Get-Content -Raw -LiteralPath $selectionPath | ConvertFrom-Json
$entries = @($selection.entries)
if ($entries.Count -eq 0) {
    throw 'The active owned schema selection is empty.'
}

Materialize-Targets $entries
Materialize-CSharpPolicy
Materialize-MigrationsAndMap $entries
Write-Output "Materialized $($entries.Count) active owned schema alpha migrations."
