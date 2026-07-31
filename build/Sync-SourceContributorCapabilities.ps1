param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[a-z][a-z0-9-]*$')]
    [string] $Provider,

    [switch] $Refresh,
    [switch] $RefreshIfStale
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$programKitRoot = Split-Path -Parent $PSScriptRoot
if ($Refresh -and $RefreshIfStale) {
    throw 'Select either -Refresh or -RefreshIfStale, not both.'
}

$markerPath = Join-Path `
    $programKitRoot `
    '.agent-capabilities/authoring-workspace.json'
$marker = Get-Content -LiteralPath $markerPath -Raw |
    ConvertFrom-Json -Depth 16

if ($marker.capabilityInitialization -ne 'denied' -or
    $marker.sourceContributorRegistration -ne 'provider-local' -or
    $marker.sourceContributorRefresh -ne 'fresh-session-or-human-request') {
    throw 'The Program Kit source-contributor marker is not the supported exact contract.'
}

$allProviderContracts = @($marker.sourceContributorProviderContracts)
$providerIds = @($allProviderContracts | ForEach-Object { [string] $_.provider })
$sortedProviderIds = @($providerIds | Sort-Object -Unique)
if ($providerIds.Count -eq 0 -or
    [string]::Join("`n", $providerIds) -ne
    [string]::Join("`n", $sortedProviderIds)) {
    throw 'Source-contributor provider IDs must be non-empty, unique, and ordinally sorted.'
}
$providerRoots = @($allProviderContracts | ForEach-Object { [string] $_.root })
if (($providerRoots | Sort-Object -Unique).Count -ne $providerRoots.Count) {
    throw 'Source-contributor provider roots must be unique.'
}
$providerContracts = @(
    $allProviderContracts |
        Where-Object { $_.provider -ceq $Provider }
)
if ($providerContracts.Count -ne 1) {
    throw "The active provider has no unique source-contributor contract: $Provider"
}
$providerContract = $providerContracts[0]
$capabilityFileName = [string] $providerContract.capabilityFileName
if ([string]::IsNullOrWhiteSpace($capabilityFileName) -or
    [IO.Path]::GetFileName($capabilityFileName) -cne $capabilityFileName) {
    throw "The registered provider capability file name is invalid: $Provider"
}

$capabilityIds = @($marker.sourceContributorCapabilities)
$sortedCapabilityIds = @($capabilityIds | Sort-Object -Unique)
if ($capabilityIds.Count -eq 0 -or
    [string]::Join("`n", $capabilityIds) -ne
    [string]::Join("`n", $sortedCapabilityIds)) {
    throw 'Source-contributor capability IDs must be non-empty, unique, and ordinally sorted.'
}

$sourceContributorRoot = [IO.Path]::GetFullPath(
    (Join-Path $programKitRoot $providerContract.root))
$providerAdapterRoot = [IO.Path]::GetFullPath(
    (Join-Path $programKitRoot $providerContract.adapterRoot))
if (-not $sourceContributorRoot.StartsWith(
        $programKitRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw "The registered provider root escapes the Program Kit workspace: $Provider"
}
if (-not $providerAdapterRoot.StartsWith(
        $programKitRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase)) {
    throw "The registered provider adapter root escapes the Program Kit workspace: $Provider"
}
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Read-NormalizedText {
    param(
        [Parameter(Mandatory)]
        [string] $Path
    )

    return [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8).
        Replace("`r`n", "`n").
        Replace("`r", "`n")
}

function Get-ProviderFrontMatter {
    param(
        [Parameter(Mandatory)]
        [string] $Path
    )

    $template = Read-NormalizedText -Path $Path
    $match = [Text.RegularExpressions.Regex]::Match(
        $template,
        '\A---\n(?<frontMatter>.*?)\n---\n',
        [Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $match.Success) {
        throw "The registered provider adapter has no exact YAML front matter: $Path"
    }

    return $match.Groups['frontMatter'].Value
}

if ($Refresh -or $RefreshIfStale) {
    [IO.Directory]::CreateDirectory($sourceContributorRoot) | Out-Null
}
elseif (-not (Test-Path -LiteralPath $sourceContributorRoot -PathType Container)) {
    throw "The source-contributor projection root is absent: $sourceContributorRoot"
}

foreach ($capabilityId in $capabilityIds) {
    $canonicalPath = Join-Path `
        $programKitRoot `
        ".agent-capabilities/capabilities/$capabilityId/CAPABILITY.md"
    $adapterPath = Join-Path `
        (Join-Path $providerAdapterRoot $capabilityId) `
        $capabilityFileName
    $projectionDirectory = Join-Path $sourceContributorRoot $capabilityId
    $projectionPath = Join-Path $projectionDirectory $capabilityFileName

    if (-not (Test-Path -LiteralPath $canonicalPath -PathType Leaf)) {
        throw "The canonical capability is absent: $canonicalPath"
    }
    if (-not (Test-Path -LiteralPath $adapterPath -PathType Leaf)) {
        throw "The registered provider adapter is absent: $adapterPath"
    }

    $frontMatter = Get-ProviderFrontMatter -Path $adapterPath
    $canonical = Read-NormalizedText -Path $canonicalPath
    $expected = "---`n$frontMatter`n---`n`n$canonical"

    $actual = if (Test-Path -LiteralPath $projectionPath -PathType Leaf) {
        Read-NormalizedText -Path $projectionPath
    }
    else {
        $null
    }

    if ($Refresh -or ($RefreshIfStale -and $actual -cne $expected)) {
        [IO.Directory]::CreateDirectory($projectionDirectory) | Out-Null
        [IO.File]::WriteAllText($projectionPath, $expected, $utf8NoBom)
        Write-Output "refreshed $capabilityId"
        continue
    }

    if ($null -eq $actual) {
        throw "The source-contributor projection is absent: $projectionPath"
    }

    if ($actual -cne $expected) {
        throw "The source-contributor projection is stale or non-exact: $projectionPath"
    }
}

$actualCapabilityIds = @(
    Get-ChildItem -LiteralPath $sourceContributorRoot -Directory |
        ForEach-Object Name |
        Sort-Object
)
if ([string]::Join("`n", $actualCapabilityIds) -ne
    [string]::Join("`n", $sortedCapabilityIds)) {
    throw 'The source-contributor projection inventory has a missing or extra capability.'
}

$unexpectedFiles = @(
    Get-ChildItem -LiteralPath $sourceContributorRoot -Recurse -File |
        Where-Object {
            $_.Name -cne $capabilityFileName -or
            $_.Directory.Parent.FullName -ne $sourceContributorRoot
        }
)
if ($unexpectedFiles.Count -gt 0) {
    throw 'The source-contributor projection root contains an unexpected file.'
}

if (-not $Refresh -and -not $RefreshIfStale) {
    Write-Output "verified $($capabilityIds.Count) source-contributor capability projections"
}
