[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ReviewRoot,

    [Parameter()]
    [ValidateRange(1024, 65535)]
    [int] $CatalogPort = 8765
)

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw 'Spec Kit adapter human review requires PowerShell 7 or later.'
}

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$requestedRoot = [IO.Path]::GetFullPath($ReviewRoot)
$parent = Split-Path -Parent $requestedRoot
$leaf = Split-Path -Leaf $requestedRoot
if (-not $parent -or -not $leaf -or -not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw 'ReviewRoot must name a new directory beneath an existing parent.'
}
$resolvedParent = (Resolve-Path -LiteralPath $parent).Path
$review = Join-Path $resolvedParent $leaf
$comparison = if ($IsWindows) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
if ($review -eq $repositoryRoot -or $review.StartsWith($repositoryRoot + [IO.Path]::DirectorySeparatorChar, $comparison)) {
    throw 'The human-review seed must be created outside the Program Kit source repository.'
}
if (Test-Path -LiteralPath $review) {
    throw 'ReviewRoot must not already exist; choose a new path for an exact fresh seed.'
}

$status = @(& git -C $repositoryRoot status --porcelain=v1 --untracked-files=normal)
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the Program Kit candidate worktree.' }
if ($status.Count -ne 0) { throw 'The Program Kit candidate worktree is not clean; commit the exact candidate before preparing human review.' }
$repositoryHead = (& git -C $repositoryRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $repositoryHead -notmatch '^[0-9a-f]{40}$') {
    throw 'Could not resolve the exact Program Kit candidate commit.'
}

$staging = Join-Path $resolvedParent ('.' + $leaf + '.staging-' + [Guid]::NewGuid().ToString('N'))
$published = $false
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Write-Utf8NoBom {
    param([Parameter(Mandatory)][string] $Path, [Parameter(Mandatory)][string] $Text)
    [IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

try {
    New-Item -ItemType Directory -Path $staging | Out-Null
    $packageBuild = Join-Path $staging '.package-build'
    $cliBuild = Join-Path $packageBuild 'cli'
    $adapterBuild = Join-Path $packageBuild 'adapter'
    New-Item -ItemType Directory -Path $cliBuild, $adapterBuild -Force | Out-Null

    & (Join-Path $PSScriptRoot 'Pack-ProgramKitTool.ps1') -OutputRoot $cliBuild
    if ($LASTEXITCODE -ne 0) { throw 'The exact Program Kit CLI package could not be prepared.' }
    & (Join-Path $PSScriptRoot 'Pack-SpecKitAdapter.ps1') -OutputRoot $adapterBuild
    if ($LASTEXITCODE -ne 0) { throw 'The exact Spec Kit adapter package could not be prepared.' }

    $feed = Join-Path $staging 'nuget-feed'
    New-Item -ItemType Directory -Path $feed | Out-Null
    $cliPackage = @(Get-ChildItem -LiteralPath $cliBuild -File -Filter 'Orbyss.ProgramKit.Cli.1.0.0-alpha.2.nupkg')
    if ($cliPackage.Count -ne 1) { throw 'The exact Program Kit CLI package output is missing or ambiguous.' }
    Copy-Item -LiteralPath $cliPackage[0].FullName -Destination $feed

    $assets = Get-Content -LiteralPath (Join-Path $repositoryRoot 'src/ProgramKit.Cli/obj/project.assets.json') -Raw |
        ConvertFrom-Json -Depth 100
    $packageFolders = @($assets.packageFolders.PSObject.Properties | ForEach-Object { $_.Name })
    foreach ($library in ($assets.libraries.PSObject.Properties | Where-Object { $_.Value.type -eq 'package' })) {
        $archives = @(
            $packageFolders |
                ForEach-Object { Join-Path $_ ([string]$library.Value.path) } |
                Where-Object { Test-Path -LiteralPath $_ -PathType Container } |
                ForEach-Object { Get-ChildItem -LiteralPath $_ -File -Filter '*.nupkg' }
        )
        if ($archives.Count -ne 1) {
            throw "The acquired CLI dependency package is unavailable or ambiguous: $($library.Name)"
        }
        Copy-Item -LiteralPath $archives[0].FullName -Destination $feed
    }

    $catalogRoot = Join-Path $staging 'catalog'
    New-Item -ItemType Directory -Path $catalogRoot | Out-Null
    $adapterArchive = Join-Path $catalogRoot 'orbyss-program-kit-adapter-0.1.0.zip'
    Copy-Item -LiteralPath (Join-Path $adapterBuild 'orbyss-program-kit-adapter-0.1.0.zip') -Destination $adapterArchive
    $cliPath = Join-Path $feed 'Orbyss.ProgramKit.Cli.1.0.0-alpha.2.nupkg'
    $cliDigest = 'sha256:' + (Get-FileHash -LiteralPath $cliPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $adapterDigest = 'sha256:' + (Get-FileHash -LiteralPath $adapterArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    $catalogUrl = "http://127.0.0.1:$CatalogPort/catalog.json"
    $archiveUrl = "http://127.0.0.1:$CatalogPort/orbyss-program-kit-adapter-0.1.0.zip"
    $extensions = [ordered]@{}
    $extensions['orbyss-program-kit-adapter'] = [ordered]@{
        name = 'Program Kit Adapter'
        version = '0.1.0'
        description = 'Exact unpublished Feature 003 human-review candidate'
        download_url = $archiveUrl
        sha256 = $adapterDigest.Substring(7)
    }
    Write-Utf8NoBom -Path (Join-Path $catalogRoot 'catalog.json') -Text (
        [ordered]@{ schema_version = '1.0'; extensions = $extensions } |
            ConvertTo-Json -Depth 10 -Compress)
    Write-Utf8NoBom -Path (Join-Path $staging 'extension-catalogs.yml') -Text (
        "catalogs:`n  - name: program-kit-human-review`n    url: $catalogUrl`n    priority: 1`n    install_allowed: true`n")

    $escapedFeed = [Security.SecurityElement]::Escape((Join-Path $review 'nuget-feed'))
    Write-Utf8NoBom -Path (Join-Path $staging 'NuGet.Config') -Text (
        "<?xml version=`"1.0`" encoding=`"utf-8`"?><configuration><packageSources><clear/><add key=`"program-kit-human-review`" value=`"$escapedFeed`"/></packageSources></configuration>")
    Write-Utf8NoBom -Path (Join-Path $staging 'global.json') -Text (
        [ordered]@{ sdk = [ordered]@{ version = '10.0.302'; rollForward = 'disable'; allowPrerelease = $false } } |
            ConvertTo-Json -Depth 5 -Compress)

    $mirrorSource = Join-Path $repositoryRoot 'artifacts/dependency-mirror'
    if (-not (Test-Path -LiteralPath (Join-Path $mirrorSource 'mirror.lock.json') -PathType Leaf)) {
        throw 'The exact governed dependency mirror is unavailable; run eng/Bootstrap-DependencyMirror.ps1 first.'
    }
    Copy-Item -LiteralPath $mirrorSource -Destination (Join-Path $staging 'dependency-mirror') -Recurse

    $consumerNames = @('consumer-01', 'consumer-02', 'consumer-03')
    foreach ($consumer in $consumerNames) {
        New-Item -ItemType Directory -Path (Join-Path $staging $consumer) | Out-Null
    }

    $environment = [ordered]@{
        schema = 'program-kit.spec-kit-adapter-human-review-seed/v1'
        status = 'ready'
        reviewRoot = $review
        candidate = [ordered]@{ repositoryHead = $repositoryHead }
        requirements = [ordered]@{
            dotnetSdk = '10.0.302'
            specKit = '0.15.1'
            programKitCli = '1.0.0-alpha.2'
            adapter = '0.1.0'
        }
        cli = [ordered]@{
            package = 'nuget-feed/Orbyss.ProgramKit.Cli.1.0.0-alpha.2.nupkg'
            digest = $cliDigest
            feedPackages = @(Get-ChildItem -LiteralPath $feed -File -Filter '*.nupkg' | Sort-Object Name | ForEach-Object { $_.Name })
        }
        adapter = [ordered]@{
            archive = 'catalog/orbyss-program-kit-adapter-0.1.0.zip'
            digest = $adapterDigest
        }
        catalog = [ordered]@{ port = $CatalogPort; catalogUrl = $catalogUrl; archiveUrl = $archiveUrl }
        dependencyMirror = 'dependency-mirror'
        consumers = $consumerNames
    }
    $environmentJson = $environment | ConvertTo-Json -Depth 20 -Compress
    Write-Utf8NoBom -Path (Join-Path $staging 'review-environment.json') -Text $environmentJson

    Remove-Item -LiteralPath $packageBuild -Recurse -Force
    foreach ($required in @('NuGet.Config', 'global.json', 'extension-catalogs.yml', 'catalog/catalog.json', 'review-environment.json')) {
        if (-not (Test-Path -LiteralPath (Join-Path $staging $required) -PathType Leaf)) {
            throw "The review seed is incomplete: $required"
        }
    }
    Move-Item -LiteralPath $staging -Destination $review
    $published = $true
    Write-Host "Spec Kit adapter human-review seed is ready at $review"
    Write-Output $environmentJson
}
finally {
    if (-not $published -and (Test-Path -LiteralPath $staging)) {
        $resolvedStaging = [IO.Path]::GetFullPath($staging)
        if ($resolvedStaging.StartsWith($resolvedParent + [IO.Path]::DirectorySeparatorChar, $comparison)) {
            Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
        }
    }
}
