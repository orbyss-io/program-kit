[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $OutputRoot
)

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

    dotnet publish (Join-Path $repositoryRoot 'src/ProgramKit.SpecKitAdapter/ProgramKit.SpecKitAdapter.csproj') `
        --configuration Release `
        --no-restore `
        --output $publishRoot `
        -p:ContinuousIntegrationBuild=true
    if ($LASTEXITCODE -ne 0) { throw 'Spec Kit adapter publish failed.' }

    $requiredFiles = @(
        'extension.yml',
        'package-manifest.json',
        'orbyss-program-kit-adapter-config.yml',
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
    [ordered]@{
        schema = 'program-kit.spec-kit-adapter-release-files/v1'
        release = 'orbyss-program-kit-adapter@0.1.0'
        ownership = 'adapter-release-owned'
        files = @($releaseFiles)
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $attemptStage 'release-files.json') -Encoding utf8NoBOM

    Compress-Archive -Path (Join-Path $attemptStage '*') -DestinationPath $attemptArchive
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
