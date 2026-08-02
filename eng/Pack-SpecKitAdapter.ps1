[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $OutputRoot,

    [Parameter()]
    [switch] $NoBuild,

    [Parameter()]
    [string] $PublishedToolsRoot
)

function Set-CanonicalZipMetadata {
    param([Parameter(Mandatory)][string] $Path)

    $bytes = [IO.File]::ReadAllBytes($Path)
    $minimumEocdOffset = [Math]::Max(0, $bytes.Length - 65557)
    $eocdOffset = -1
    for ($candidate = $bytes.Length - 22; $candidate -ge $minimumEocdOffset; $candidate--) {
        if ([BitConverter]::ToUInt32($bytes, $candidate) -eq 0x06054b50) {
            $eocdOffset = $candidate
            break
        }
    }
    if ($eocdOffset -lt 0) { throw 'The staged adapter archive has no ZIP end-of-central-directory record.' }

    $entryCount = [BitConverter]::ToUInt16($bytes, $eocdOffset + 10)
    $entryOffset = [BitConverter]::ToUInt32($bytes, $eocdOffset + 16)
    for ($entryIndex = 0; $entryIndex -lt $entryCount; $entryIndex++) {
        if ([BitConverter]::ToUInt32($bytes, $entryOffset) -ne 0x02014b50) {
            throw "The staged adapter archive has an invalid central-directory entry at index $entryIndex."
        }
        $bytes[$entryOffset + 5] = 0
        $bytes[$entryOffset + 38] = 0
        $bytes[$entryOffset + 39] = 0
        $bytes[$entryOffset + 40] = 0
        $bytes[$entryOffset + 41] = 0
        $nameLength = [BitConverter]::ToUInt16($bytes, $entryOffset + 28)
        $extraLength = [BitConverter]::ToUInt16($bytes, $entryOffset + 30)
        $commentLength = [BitConverter]::ToUInt16($bytes, $entryOffset + 32)
        $entryOffset += 46 + $nameLength + $extraLength + $commentLength
    }
    [IO.File]::WriteAllBytes($Path, $bytes)
}

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$resolvedOutput = if ([IO.Path]::IsPathRooted($OutputRoot)) {
    [IO.Path]::GetFullPath($OutputRoot)
}
else {
    [IO.Path]::GetFullPath((Join-Path $repositoryRoot $OutputRoot))
}
$releaseName = 'orbyss-program-kit-adapter-0.1.0'
$stageRoot = Join-Path $resolvedOutput $releaseName
$archivePath = Join-Path $resolvedOutput "$releaseName.zip"
$attemptRoot = Join-Path $resolvedOutput ".staging-$([Guid]::NewGuid().ToString('N'))"
$attemptStage = Join-Path $attemptRoot $releaseName
$attemptArchive = Join-Path $attemptRoot "$releaseName.zip"
$publishRoot = Join-Path $attemptStage 'tools'
$stageBackup = Join-Path $attemptRoot 'prior-stage'
$archiveBackup = Join-Path $attemptRoot 'prior-archive.zip'

New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
New-Item -ItemType Directory -Path $attemptRoot | Out-Null
$activationComplete = $false
try {
    Copy-Item -LiteralPath (Join-Path $repositoryRoot 'extensions/orbyss-program-kit-adapter') -Destination $attemptStage -Recurse
    $configTemplate = Join-Path $attemptStage 'config/orbyss-program-kit-adapter-config.template.yml'
    $projectConfig = Join-Path $attemptStage 'orbyss-program-kit-adapter-config.yml'
    Copy-Item -LiteralPath $configTemplate -Destination $projectConfig
    Copy-Item -LiteralPath (Join-Path $repositoryRoot 'src/ProgramKit.SpecKitAdapter/Schemas') -Destination (Join-Path $attemptStage 'schemas') -Recurse
    Copy-Item -LiteralPath (Join-Path $repositoryRoot 'src/ProgramKit.SpecKitAdapter/Resources/compatibility.json') -Destination (Join-Path $attemptStage 'compatibility.json')
    Copy-Item -LiteralPath (Join-Path $repositoryRoot 'src/ProgramKit.SpecKitAdapter/Resources/diagnostic-catalog.json') -Destination (Join-Path $attemptStage 'diagnostic-catalog.json')

    if ($PublishedToolsRoot) {
        $resolvedTools = [IO.Path]::GetFullPath($PublishedToolsRoot)
        if (-not (Test-Path -LiteralPath (Join-Path $resolvedTools 'program-kit-spec-kit-adapter.dll') -PathType Leaf)) {
            throw 'The supplied published adapter tools are incomplete.'
        }
        New-Item -ItemType Directory -Path $publishRoot | Out-Null
        Copy-Item -Path (Join-Path $resolvedTools '*') -Destination $publishRoot -Recurse
    }
    else {
        $adapterProject = Join-Path $repositoryRoot 'src/ProgramKit.SpecKitAdapter/ProgramKit.SpecKitAdapter.csproj'
        $releaseProperties = @(
            '-p:ContinuousIntegrationBuild=true',
            '-p:DebugSymbols=false',
            '-p:DebugType=None',
            '-p:IncludeSourceRevisionInInformationalVersion=false',
            '-p:NoWin32Manifest=true',
            "-p:PathMap=$repositoryRoot=/_/"
        )
        if (-not $NoBuild) {
            $buildArguments = @(
                'build',
                $adapterProject,
                '--configuration', 'Release',
                '--no-restore',
                '--no-incremental'
            ) + $releaseProperties
            & dotnet @buildArguments
            if ($LASTEXITCODE -ne 0) { throw 'Spec Kit adapter release build failed.' }
        }
        $publishArguments = @(
            'publish',
            $adapterProject,
            '--configuration', 'Release',
            '--no-restore',
            '--no-build',
            '--output', $publishRoot,
            $releaseProperties
        )
        & dotnet @publishArguments
        if ($LASTEXITCODE -ne 0) { throw 'Spec Kit adapter publish failed.' }
    }
    Get-ChildItem -LiteralPath $publishRoot -File | Where-Object { $_.Extension -In @('.pdb', '.xml', '.exe') } | Remove-Item -Force
    $utf8NoBom = [Text.UTF8Encoding]::new($false, $true)
    foreach ($generatedJson in (Get-ChildItem -LiteralPath $publishRoot -File -Filter '*.json')) {
        $jsonText = [IO.File]::ReadAllText($generatedJson.FullName, $utf8NoBom)
        $normalizedJson = $jsonText.Replace("`r`n", "`n").Replace("`r", "`n")
        [IO.File]::WriteAllText($generatedJson.FullName, $normalizedJson, $utf8NoBom)
    }

    $requiredFiles = @(
        'extension.yml',
        'package-manifest.json',
        'orbyss-program-kit-adapter-config.yml',
        'compatibility.json',
        'diagnostic-catalog.json',
        'schemas/adapter-result.schema.json',
        'tools/program-kit-spec-kit-adapter.dll',
        'tools/program-kit-spec-kit-adapter.runtimeconfig.json'
    )
    foreach ($logicalPath in $requiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $attemptStage $logicalPath) -PathType Leaf)) {
            throw "Incomplete Spec Kit adapter package: $logicalPath is missing."
        }
    }

    $releaseFiles = Get-ChildItem -LiteralPath $attemptStage -Recurse -File |
        Sort-Object { [IO.Path]::GetRelativePath($attemptStage, $_.FullName).Replace('\', '/') } |
        ForEach-Object {
            [ordered]@{
                logicalPath = [IO.Path]::GetRelativePath($attemptStage, $_.FullName).Replace('\', '/')
                digest = 'sha256:' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        }
    $releaseFilesDocument = [ordered]@{
        schema = 'program-kit.spec-kit-adapter-release-files/v1'
        release = 'orbyss-program-kit-adapter@0.1.0'
        ownership = 'adapter-release-owned'
        files = @($releaseFiles)
    }
    $releaseFilesJson = $releaseFilesDocument | ConvertTo-Json -Depth 6 -Compress
    [IO.File]::WriteAllText((Join-Path $attemptStage 'release-files.json'), $releaseFilesJson, [Text.UTF8Encoding]::new($false))

    $archiveStream = [IO.File]::Open($attemptArchive, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    try {
        $archive = [IO.Compression.ZipArchive]::new($archiveStream, [IO.Compression.ZipArchiveMode]::Create, $true)
        try {
            foreach ($file in (Get-ChildItem -LiteralPath $attemptStage -Recurse -File | Sort-Object { [IO.Path]::GetRelativePath($attemptStage, $_.FullName).Replace('\', '/') })) {
                $logicalPath = [IO.Path]::GetRelativePath($attemptStage, $file.FullName).Replace('\', '/')
                $entry = $archive.CreateEntry($logicalPath, [IO.Compression.CompressionLevel]::NoCompression)
                $entry.LastWriteTime = [DateTimeOffset]::new(1980, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
                $entry.ExternalAttributes = 0
                $source = $file.OpenRead()
                $destination = $entry.Open()
                try { $source.CopyTo($destination) }
                finally {
                    $destination.Dispose()
                    $source.Dispose()
                }
            }
        }
        finally { $archive.Dispose() }
    }
    finally { $archiveStream.Dispose() }
    Set-CanonicalZipMetadata -Path $attemptArchive
    if (-not (Test-Path -LiteralPath $attemptArchive -PathType Leaf)) {
        throw 'Spec Kit adapter archive staging failed.'
    }

    $stageBackedUp = $false
    $archiveBackedUp = $false
    try {
        if (Test-Path -LiteralPath $stageRoot) {
            Move-Item -LiteralPath $stageRoot -Destination $stageBackup
            $stageBackedUp = $true
        }
        if (Test-Path -LiteralPath $archivePath) {
            Move-Item -LiteralPath $archivePath -Destination $archiveBackup
            $archiveBackedUp = $true
        }
        Move-Item -LiteralPath $attemptStage -Destination $stageRoot
        Move-Item -LiteralPath $attemptArchive -Destination $archivePath
        $activationComplete = $true
    }
    catch {
        if (Test-Path -LiteralPath $stageRoot) { Remove-Item -LiteralPath $stageRoot -Recurse -Force }
        if (Test-Path -LiteralPath $archivePath) { Remove-Item -LiteralPath $archivePath -Force }
        if ($stageBackedUp -and (Test-Path -LiteralPath $stageBackup)) { Move-Item -LiteralPath $stageBackup -Destination $stageRoot }
        if ($archiveBackedUp -and (Test-Path -LiteralPath $archiveBackup)) { Move-Item -LiteralPath $archiveBackup -Destination $archivePath }
        throw
    }

    [pscustomobject]@{ StageRoot = $stageRoot; ArchivePath = $archivePath } | ConvertTo-Json -Compress
}
finally {
    $recoveryMaterialRemains = (Test-Path -LiteralPath $stageBackup) -or (Test-Path -LiteralPath $archiveBackup)
    if ((Test-Path -LiteralPath $attemptRoot) -and ($activationComplete -or -not $recoveryMaterialRemains)) {
        Remove-Item -LiteralPath $attemptRoot -Recurse -Force
    }
}
