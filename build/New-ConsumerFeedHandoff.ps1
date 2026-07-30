[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ConsumerFeedRoot,

    [Parameter(Mandatory = $true)]
    [string] $OutputRoot
)

$ErrorActionPreference = 'Stop'
$feedRoot = [IO.Path]::GetFullPath($ConsumerFeedRoot)
$outputPath = [IO.Path]::GetFullPath($OutputRoot)
$packageDirectory = Join-Path $feedRoot 'feed'
$packageManifestPath = Join-Path $feedRoot 'package-manifest.json'
$checksumsPath = Join-Path $feedRoot 'SHA256SUMS'
if (-not (Test-Path -LiteralPath $packageDirectory -PathType Container) -or
    -not (Test-Path -LiteralPath $packageManifestPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $checksumsPath -PathType Leaf)) {
    throw 'The consumer-feed root must contain feed/, package-manifest.json, and SHA256SUMS.'
}

if (Test-Path -LiteralPath $outputPath) {
    throw "The handoff output must be a new path: $outputPath"
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    return "sha256:$((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant())"
}

function Write-Utf8Text {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $Text
    )

    [IO.File]::WriteAllText(
        $Path,
        $Text.Replace("`r`n", "`n"),
        [Text.UTF8Encoding]::new($false))
}

$manifest = [IO.File]::ReadAllText($packageManifestPath) | ConvertFrom-Json
$version = [string] $manifest.productVersion
if ($version -cnotmatch '^0\.1\.0-alpha\.[1-9][0-9]*$') {
    throw 'The package manifest does not select one exact Program Kit alpha version.'
}

$expectedPackages = @($manifest.packages | Sort-Object filename)
$actualPackages = @(
    Get-ChildItem -LiteralPath $packageDirectory -Filter '*.nupkg' -File |
        Sort-Object Name)
if (($expectedPackages.filename -join "`n") -cne
    ($actualPackages.Name -join "`n")) {
    throw 'The flat feed package set does not match package-manifest.json.'
}

foreach ($package in $expectedPackages) {
    $path = Join-Path $packageDirectory $package.filename
    if ($package.version -cne $version -or
        (Get-Sha256 $path) -cne $package.sha256 -or
        (Get-Item -LiteralPath $path).Length -ne $package.size) {
        throw "Package evidence does not match for $($package.filename)."
    }
}

$expectedChecksumRows = @(
    $expectedPackages |
        ForEach-Object {
            "$($_.sha256.Substring(7))  feed/$($_.filename)"
        })
$expectedChecksumRows += "$(
    (Get-Sha256 $packageManifestPath).Substring(7)
)  package-manifest.json"
$actualChecksumRows = @(
    [IO.File]::ReadAllLines($checksumsPath) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ((($expectedChecksumRows | Sort-Object) -join "`n") -cne
    (($actualChecksumRows | Sort-Object) -join "`n")) {
    throw 'SHA256SUMS does not match the exact package and manifest bytes.'
}

$outputParent = Split-Path -Parent $outputPath
if (-not (Test-Path -LiteralPath $outputParent -PathType Container)) {
    throw "The handoff output parent must already exist: $outputParent"
}

$stagePath = Join-Path $outputParent (
    ".program-kit-consumer-handoff-$([guid]::NewGuid().ToString('N'))")
try {
    New-Item -ItemType Directory -Path $stagePath | Out-Null
    $promptPath = Join-Path $stagePath 'JTEST-PROMPT.md'
    $prompt = @'
# JTest package-only Program Kit initialization

You are in the clean JTest repository root. Install and initialize Program Kit
`{VERSION}` only from the human-supplied, extracted handoff archive. Do not clone
the Program Kit repository, add a submodule, inspect Program Kit assemblies, or
read Program Kit source/test fixtures.

1. Resolve the extracted archive's `feed` directory and verify every row in
   `SHA256SUMS` before installing anything. Stop on any missing or mismatched
   byte.
2. Create a bounded temporary NuGet configuration that maps
   `Orbyss.ProgramKit.*` only to that local `feed` directory and maps external
   dependencies only to `https://api.nuget.org/v3/index.json`. Do not modify the
   machine's permanent NuGet configuration and do not use
   `--ignore-failed-sources`.
3. Inspect `dotnet tool list --global`. Install
   `Orbyss.ProgramKit.CommandLine` globally at exactly `{VERSION}`, or update an
   existing Program Kit tool to exactly that version, using the temporary
   configuration, `--no-cache`, and no `latest` range. Stop if the installed
   version is not exactly `{VERSION}`.
4. Run `program-kit --help`.
5. Initialize the provider that is actually running this session:
   - Codex: `program-kit capabilities initialize --provider codex --workspace-root .`
   - Claude: `program-kit capabilities initialize --provider claude --workspace-root .`
   Do not guess a different provider and do not initialize both unless the
   human asks for both.
6. Run `program-kit capabilities catalog --workspace-root . --format text`,
   then `program-kit capabilities preflight develop-software --workspace-root . --format text`.
7. Confirm the generated provider wrappers invoke `program-kit capabilities
   preflight` and `program-kit capabilities read`, the workspace lock records
   CLI version `{VERSION}`, and no wrapper points to a Program Kit checkout.
8. Do not hand-edit Program Kit-owned wrappers, locks, generated hosts,
   materialized Console inputs, gate bind requests, or selection locks. Use the
   backed CLI commands named by the retrieved capability. If anything is
   missing, stale, invalid, or not discoverable, stop and report the exact
   command, exit code, stdout, and stderr rather than working around it.

Report the installed tool version, selected provider, initialization outcome,
catalog/preflight state, lock path, and every rough edge. Do not start unrelated
JTest product changes during this initialization check.
'@
    $prompt = $prompt.Replace(
        '{VERSION}',
        $version,
        [StringComparison]::Ordinal)
    Write-Utf8Text -Path $promptPath -Text "$prompt`n"
    Copy-Item -LiteralPath $packageManifestPath -Destination $stagePath
    Copy-Item -LiteralPath $checksumsPath -Destination $stagePath

    Add-Type -AssemblyName System.IO.Compression
    $archiveName = "orbyss-program-kit-nuget-$version.zip"
    $archivePath = Join-Path $stagePath $archiveName
    $stream = [IO.FileStream]::new(
        $archivePath,
        [IO.FileMode]::CreateNew,
        [IO.FileAccess]::Write,
        [IO.FileShare]::None)
    try {
        $archive = [IO.Compression.ZipArchive]::new(
            $stream,
            [IO.Compression.ZipArchiveMode]::Create,
            $true,
            [Text.UTF8Encoding]::new($false))
        try {
            $entries =
                [Collections.Generic.SortedDictionary[string, string]]::new(
                    [StringComparer]::Ordinal)
            foreach ($package in $actualPackages) {
                $entries.Add(
                    "feed/$($package.Name)",
                    $package.FullName)
            }

            $entries.Add('package-manifest.json', $packageManifestPath)
            $entries.Add('SHA256SUMS', $checksumsPath)
            $entries.Add('JTEST-PROMPT.md', $promptPath)
            foreach ($entryInput in $entries.GetEnumerator()) {
                $entry = $archive.CreateEntry(
                    $entryInput.Key,
                    [IO.Compression.CompressionLevel]::Optimal)
                $entry.LastWriteTime = [DateTimeOffset]::new(
                    1980,
                    1,
                    1,
                    0,
                    0,
                    0,
                    [TimeSpan]::Zero)
                $entryStream = $entry.Open()
                $inputStream = [IO.File]::OpenRead($entryInput.Value)
                try {
                    $inputStream.CopyTo($entryStream)
                }
                finally {
                    $inputStream.Dispose()
                    $entryStream.Dispose()
                }
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $stream.Dispose()
    }

    $archiveDigest = Get-Sha256 $archivePath
    Write-Utf8Text `
        -Path (Join-Path $stagePath "$archiveName.sha256") `
        -Text "$($archiveDigest.Substring(7))  $archiveName`n"
    $handoffManifest = [ordered]@{
        manifestVersion = '0.1.0-alpha.1'
        productVersion = $version
        packageCount = $expectedPackages.Count
        packageManifestSha256 = Get-Sha256 $packageManifestPath
        checksumsSha256 = Get-Sha256 $checksumsPath
        promptSha256 = Get-Sha256 $promptPath
        archive = [ordered]@{
            filename = $archiveName
            sha256 = $archiveDigest
            size = (Get-Item -LiteralPath $archivePath).Length
        }
    }
    Write-Utf8Text `
        -Path (Join-Path $stagePath 'handoff-manifest.json') `
        -Text "$($handoffManifest | ConvertTo-Json -Depth 6)`n"

    if (Test-Path -LiteralPath $outputPath) {
        throw "The handoff output appeared during the transaction: $outputPath"
    }

    Move-Item -LiteralPath $stagePath -Destination $outputPath
    Write-Output (
        "Program Kit consumer handoff created: version=$version packages=$(
            $expectedPackages.Count) output=$outputPath")
}
finally {
    if (Test-Path -LiteralPath $stagePath) {
        $resolvedStage = [IO.Path]::GetFullPath($stagePath)
        $resolvedParent = [IO.Path]::GetFullPath($outputParent).TrimEnd(
            [IO.Path]::DirectorySeparatorChar)
        if (-not $resolvedStage.StartsWith(
                "$resolvedParent$([IO.Path]::DirectorySeparatorChar)",
                [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean a staging path outside the output parent: $resolvedStage"
        }

        Remove-Item -LiteralPath $resolvedStage -Recurse -Force
    }
}
