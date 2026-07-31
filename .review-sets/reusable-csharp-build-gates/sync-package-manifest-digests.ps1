#requires -Version 7.4

<#
.SYNOPSIS
Verifies or records reusable C# build-gate package-manifest digests.

.DESCRIPTION
Inventory content is read as exact Git index blobs so .gitattributes clean
filters, including LF normalization, have already been applied. Stage changed
inventory inputs before using -Update. Update mode writes LF-only UTF-8
manifests and rebinds their exact bytes in the package version maps and
compatibility matrix. Without -Update, the script is a fail-closed verifier.
#>

[CmdletBinding()]
param(
    [switch] $Update,
    [string] $RepositoryRoot
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = [IO.Path]::GetFullPath(
        (Join-Path $PSScriptRoot '..\..'))
}
$utf8NoBom = [Text.UTF8Encoding]::new(
    $false,
    $true)
$digestAlgorithm = 'sha256(path-utf8,0,file-bytes,0)'
$zero = [byte[]] @(0)
$matrixRelativePath =
    'extensions/reusable-csharp-build-gates/compatibility-version-matrix.json'
$specifications = @(
    [pscustomobject] @{
        Manifest = 'authoring-package-manifest.json'
        Inventories = @('sourceInventory')
        VersionMap = 'authoring-version-map.json'
        VersionMapBindingCount = 5
        MatrixBindingCount = 0
    },
    [pscustomobject] @{
        Manifest = 'build-package-manifest.json'
        Inventories = @('sourceInventory')
        VersionMap = 'build-version-map.json'
        VersionMapBindingCount = 5
        MatrixBindingCount = 2
    },
    [pscustomobject] @{
        Manifest = 'testing-package-manifest.json'
        Inventories = @(
            'sourceInventory',
            'operationSourceInventory')
        VersionMap = 'testing-version-map.json'
        VersionMapBindingCount = 8
        MatrixBindingCount = 2
    }
)

function Assert-Condition(
    [bool] $Condition,
    [string] $Message
) {
    if (-not $Condition) {
        throw $Message
    }
}

function Get-StrictLfText([string] $Path) {
    Assert-Condition (Test-Path -LiteralPath $Path -PathType Leaf) (
        "Required digest input '$Path' does not exist.")
    $bytes = [IO.File]::ReadAllBytes($Path)
    Assert-Condition (
        $bytes.Length -lt 3 -or
        -not (
            $bytes[0] -eq 0xEF -and
            $bytes[1] -eq 0xBB -and
            $bytes[2] -eq 0xBF
        )
    ) "Digest input '$Path' has a UTF-8 byte-order mark."

    $text = $utf8NoBom.GetString($bytes)
    $text = $text.Replace("`r`n", "`n")
    Assert-Condition (-not $text.Contains("`r")) (
        "Digest input '$Path' has unsupported carriage-return bytes.")
    return $text
}

function Get-Sha256([byte[]] $Bytes) {
    return 'sha256:' + [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Bytes)
    ).ToLowerInvariant()
}

function Get-OccurrenceCount(
    [string] $Text,
    [string] $Value
) {
    $count = 0
    $offset = 0
    while (($offset = $Text.IndexOf(
        $Value,
        $offset,
        [StringComparison]::Ordinal)) -ge 0) {
        $count++
        $offset += $Value.Length
    }

    return $count
}

function Assert-SafeGitPath([string] $RelativePath) {
    Assert-Condition (
        -not [string]::IsNullOrWhiteSpace($RelativePath) -and
        -not [IO.Path]::IsPathRooted($RelativePath) -and
        -not $RelativePath.Contains('\') -and
        @($RelativePath.Split('/') | Where-Object {
            [string]::IsNullOrWhiteSpace($_) -or $_ -in @('.', '..')
        }).Count -eq 0
    ) "Inventory path '$RelativePath' is not a safe normalized Git path."
}

function Read-GitIndexBytes([string] $RelativePath) {
    Assert-SafeGitPath $RelativePath

    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = 'git'
    $startInfo.WorkingDirectory = $RepositoryRoot
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    foreach ($argument in @(
        '-c',
        ('safe.directory=' + $RepositoryRoot.Replace('\', '/')),
        '-C',
        $RepositoryRoot,
        'show',
        '--no-ext-diff',
        '--no-textconv',
        (':' + $RelativePath)
    )) {
        $startInfo.ArgumentList.Add($argument)
    }

    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $output = [IO.MemoryStream]::new()
    try {
        Assert-Condition $process.Start() (
            "Could not start Git while reading '$RelativePath'.")
        $copyTask = $process.StandardOutput.BaseStream.CopyToAsync($output)
        $errorTask = $process.StandardError.ReadToEndAsync()
        $process.WaitForExit()
        $null = $copyTask.GetAwaiter().GetResult()
        $errorText = $errorTask.GetAwaiter().GetResult()
        Assert-Condition ($process.ExitCode -eq 0) (
            "Git could not read the normalized index bytes for " +
            "'$RelativePath'. Stage every inventory input before recording. " +
            $errorText.Trim())
        return ,$output.ToArray()
    }
    finally {
        $output.Dispose()
        $process.Dispose()
    }
}

function Get-Inventory(
    [string] $ManifestText,
    [string] $InventoryName,
    [string] $ManifestName
) {
    $bytes = $utf8NoBom.GetBytes($ManifestText)
    $document = [Text.Json.JsonDocument]::Parse(
        [ReadOnlyMemory[byte]]::new($bytes))
    try {
        $inventory = $document.RootElement.GetProperty($InventoryName)
        $algorithm = $inventory.GetProperty(
            'digestAlgorithm').GetString()
        Assert-Condition ($algorithm -eq $digestAlgorithm) (
            "'$ManifestName/$InventoryName' uses unsupported digest " +
            "algorithm '$algorithm'.")
        $recordedDigest = $inventory.GetProperty('digest').GetString()
        Assert-Condition (
            $recordedDigest -match '^sha256:[0-9a-f]{64}$'
        ) "'$ManifestName/$InventoryName' has an invalid recorded digest."

        $paths = @(
            $inventory.GetProperty('paths').EnumerateArray() |
                ForEach-Object {
                    $_.GetString()
                }
        )
        Assert-Condition (
            $paths.Count -gt 0 -and
            @($paths | Where-Object {
                [string]::IsNullOrWhiteSpace($_)
            }).Count -eq 0
        ) "'$ManifestName/$InventoryName' has an empty inventory path."
        $sortedPaths = [string[]] $paths.Clone()
        [Array]::Sort($sortedPaths, [StringComparer]::Ordinal)
        for ($index = 0; $index -lt $paths.Count; $index++) {
            Assert-Condition (
                [string]::Equals(
                    $paths[$index],
                    $sortedPaths[$index],
                    [StringComparison]::Ordinal)
            ) "'$ManifestName/$InventoryName' paths are not ordinal-sorted."
        }
        $uniquePaths = [Collections.Generic.HashSet[string]]::new(
            [StringComparer]::Ordinal)
        foreach ($path in $paths) {
            Assert-Condition ($uniquePaths.Add($path)) (
                "'$ManifestName/$InventoryName' contains duplicate path " +
                "'$path'.")
        }

        return [pscustomobject] @{
            RecordedDigest = $recordedDigest
            Paths = [string[]] $paths
        }
    }
    finally {
        $document.Dispose()
    }
}

function Get-InventoryDigest([string[]] $Paths) {
    $hash = [Security.Cryptography.IncrementalHash]::CreateHash(
        [Security.Cryptography.HashAlgorithmName]::SHA256)
    try {
        foreach ($relativePath in $Paths) {
            $hash.AppendData([Text.Encoding]::UTF8.GetBytes($relativePath))
            $hash.AppendData($zero)
            $hash.AppendData((Read-GitIndexBytes $relativePath))
            $hash.AppendData($zero)
        }

        return 'sha256:' + [Convert]::ToHexString(
            $hash.GetHashAndReset()).ToLowerInvariant()
    }
    finally {
        $hash.Dispose()
    }
}

$repository = [IO.Path]::TrimEndingDirectorySeparator(
    [IO.Path]::GetFullPath($RepositoryRoot))
$pathComparison = if ($IsWindows) {
    [StringComparison]::OrdinalIgnoreCase
}
else {
    [StringComparison]::Ordinal
}
Assert-Condition (Test-Path -LiteralPath $repository -PathType Container) (
    "Repository root '$repository' does not exist.")
$extensionRoot = [IO.Path]::GetFullPath($PSScriptRoot)
Assert-Condition (
    $extensionRoot.StartsWith(
        $repository + [IO.Path]::DirectorySeparatorChar,
        $pathComparison)
) "The digest flow must remain inside the selected repository."

$matrixPath = Join-Path $repository $matrixRelativePath
$matrixText = Get-StrictLfText $matrixPath
$originalMatrixText = $matrixText
$pendingWrites = [ordered] @{}

foreach ($specification in $specifications) {
    $manifestPath = Join-Path $extensionRoot $specification.Manifest
    $versionMapPath = Join-Path $extensionRoot $specification.VersionMap
    $manifestText = Get-StrictLfText $manifestPath
    $versionMapText = Get-StrictLfText $versionMapPath
    $originalManifestText = $manifestText
    $originalVersionMapText = $versionMapText
    $oldManifestDigest = Get-Sha256 ($utf8NoBom.GetBytes($manifestText))

    Assert-Condition (
        (Get-OccurrenceCount $versionMapText $oldManifestDigest) -eq
            $specification.VersionMapBindingCount
    ) (
        "'$($specification.VersionMap)' does not exactly bind the current " +
        "normalized bytes of '$($specification.Manifest)'.")
    Assert-Condition (
        (Get-OccurrenceCount $matrixText $oldManifestDigest) -eq
            $specification.MatrixBindingCount
    ) (
        "'compatibility-version-matrix.json' does not contain the expected " +
        "bindings for '$($specification.Manifest)'.")

    foreach ($inventoryName in $specification.Inventories) {
        $inventory = Get-Inventory `
            $manifestText `
            $inventoryName `
            $specification.Manifest
        $actualDigest = Get-InventoryDigest $inventory.Paths

        if (-not $Update) {
            Assert-Condition (
                $inventory.RecordedDigest -eq $actualDigest
            ) (
                "'$($specification.Manifest)/$inventoryName' records " +
                "'$($inventory.RecordedDigest)' but Git-normalized index " +
                "bytes produce '$actualDigest'.")
            Write-Output (
                "PASS $($specification.Manifest)/$inventoryName " +
                $actualDigest)
            continue
        }

        Assert-Condition (
            (Get-OccurrenceCount `
                $manifestText `
                $inventory.RecordedDigest) -eq 1
        ) (
            "'$($specification.Manifest)/$inventoryName' digest is not one " +
            "unambiguous manifest value.")
        $manifestText = $manifestText.Replace(
            $inventory.RecordedDigest,
            $actualDigest,
            [StringComparison]::Ordinal)
    }

    if ($Update) {
        $newManifestDigest = Get-Sha256 ($utf8NoBom.GetBytes($manifestText))
        $versionMapText = $versionMapText.Replace(
            $oldManifestDigest,
            $newManifestDigest,
            [StringComparison]::Ordinal)
        $matrixText = $matrixText.Replace(
            $oldManifestDigest,
            $newManifestDigest,
            [StringComparison]::Ordinal)
        if (-not [string]::Equals(
            $manifestText,
            $originalManifestText,
            [StringComparison]::Ordinal
        )) {
            $pendingWrites[$manifestPath] = $manifestText
            Write-Output (
                "UPDATED $($specification.Manifest) $newManifestDigest")
        }
        else {
            Write-Output (
                "UNCHANGED $($specification.Manifest) $newManifestDigest")
        }
        if (-not [string]::Equals(
            $versionMapText,
            $originalVersionMapText,
            [StringComparison]::Ordinal
        )) {
            $pendingWrites[$versionMapPath] = $versionMapText
        }
    }
}

if ($Update) {
    if (-not [string]::Equals(
        $matrixText,
        $originalMatrixText,
        [StringComparison]::Ordinal
    )) {
        $pendingWrites[$matrixPath] = $matrixText
    }
    foreach ($entry in $pendingWrites.GetEnumerator()) {
        [IO.File]::WriteAllText(
            [string] $entry.Key,
            [string] $entry.Value,
            $utf8NoBom)
    }
}
