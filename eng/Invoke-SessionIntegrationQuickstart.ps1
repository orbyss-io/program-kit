[CmdletBinding()]
param(
    [ValidateRange(10, 10)]
    [int] $Trials = 10,

    [string] $EvidencePath = 'specs/002-session-integration-proof/reviews/deterministic-session-review.json',

    [switch] $SkipBootstrap
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$temporaryBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar)
$temporaryRoot = [IO.Path]::GetFullPath((Join-Path $temporaryBase (Join-Path 'program-kit-session-quickstart' ([guid]::NewGuid().ToString('N')))))
$evidence = if ([IO.Path]::IsPathRooted($EvidencePath)) {
    [IO.Path]::GetFullPath($EvidencePath)
}
else {
    [IO.Path]::GetFullPath((Join-Path $repositoryRoot $EvidencePath))
}

if (-not $temporaryRoot.StartsWith($temporaryBase + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to create a quickstart root outside the system temporary directory: $temporaryRoot"
}
if ($temporaryRoot.StartsWith($repositoryRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'The consumer quickstart root must remain outside the Program Kit source repository.'
}

$feed = Join-Path $temporaryRoot 'feed'
New-Item -ItemType Directory -Path $feed -Force | Out-Null
$previousFeed = $env:PROGRAM_KIT_SESSION_FEED
$previousEvidence = $env:PROGRAM_KIT_SESSION_REVIEW_OUTPUT
$previousTelemetry = $env:DOTNET_CLI_TELEMETRY_OPTOUT
$previousAppData = $env:APPDATA
$previousXdgConfig = $env:XDG_CONFIG_HOME
$previousDotnetHome = $env:DOTNET_CLI_HOME
$previousNodeReuse = $env:MSBUILDDISABLENODEREUSE
$previousBuildServer = $env:DOTNET_CLI_USE_MSBUILD_SERVER
$previousPackages = $env:NUGET_PACKAGES

Push-Location $repositoryRoot
try {
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    if (-not $SkipBootstrap) {
        & (Join-Path $PSScriptRoot 'Bootstrap-DependencyMirror.ps1')
        if ($LASTEXITCODE -ne 0) { throw 'Dependency mirror bootstrap failed.' }
    }

    $processAppData = Join-Path $temporaryRoot 'process-appdata'
    New-Item -ItemType Directory -Path (Join-Path $processAppData 'NuGet') -Force | Out-Null
    $env:APPDATA = $processAppData
    $env:XDG_CONFIG_HOME = $processAppData
    $env:DOTNET_CLI_HOME = Join-Path $temporaryRoot 'process-home'
    $env:MSBUILDDISABLENODEREUSE = '1'
    $env:NUGET_PACKAGES = Join-Path $repositoryRoot 'packages/cache'
    $env:DOTNET_CLI_USE_MSBUILD_SERVER = '0'
    dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.Config
    if ($LASTEXITCODE -ne 0) { throw 'Locked restore failed.' }
    dotnet build ProgramKit.slnx --configuration Release --no-restore
    if ($LASTEXITCODE -ne 0) { throw 'Release build failed.' }
    dotnet format ProgramKit.slnx --no-restore --verify-no-changes
    if ($LASTEXITCODE -ne 0) { throw 'Formatting verification failed.' }

    & (Join-Path $PSScriptRoot 'Pack-ProgramKitTool.ps1') -OutputRoot $feed
    if ($LASTEXITCODE -ne 0) { throw 'Program Kit package acquisition failed.' }

    $env:PROGRAM_KIT_SESSION_FEED = $feed
    $env:PROGRAM_KIT_SESSION_REVIEW_OUTPUT = $evidence
    dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj `
        --configuration Release `
        --no-build `
        --no-restore `
        --filter DeterministicSessionReviewAcceptanceTests `
        --verbosity minimal
    if ($LASTEXITCODE -ne 0) { throw 'The deterministic ten-workspace session review failed.' }

    if (-not (Test-Path -LiteralPath $evidence -PathType Leaf)) { throw 'The deterministic review did not produce its bounded evidence record.' }
    $review = Get-Content -LiteralPath $evidence -Raw | ConvertFrom-Json -Depth 100
    if ($review.trials.Count -ne $Trials) { throw "Expected $Trials review trials but observed $($review.trials.Count)." }
    if ($review.failures.Count -ne 0 -or -not $review.assertions.allTrialsPassed) { throw 'The deterministic review contains a failure.' }
    if (-not $review.assertions.networkDeniedAfterAcquisition -or -not $review.assertions.telemetryDisabled) { throw 'The deterministic review did not prove its network and telemetry boundary.' }
    if ($review.assertions.sourceUploadObserved -or $review.assertions.providerGlobalRegistrationObserved) { throw 'The deterministic review observed a prohibited external effect.' }

    Write-Host "Deterministic session review passed: $($review.trials.Count) workspaces"
    Write-Host "Package digest: $($review.packageDigest)"
    Write-Host "Evidence: $evidence"
}
finally {
    Pop-Location
    $env:APPDATA = $previousAppData
    $env:XDG_CONFIG_HOME = $previousXdgConfig
    $env:DOTNET_CLI_HOME = $previousDotnetHome
    $env:MSBUILDDISABLENODEREUSE = $previousNodeReuse
    $env:NUGET_PACKAGES = $previousPackages
    $env:DOTNET_CLI_USE_MSBUILD_SERVER = $previousBuildServer
    $env:PROGRAM_KIT_SESSION_FEED = $previousFeed
    $env:PROGRAM_KIT_SESSION_REVIEW_OUTPUT = $previousEvidence
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = $previousTelemetry
    $resolvedCleanup = [IO.Path]::GetFullPath($temporaryRoot)
    if (-not $resolvedCleanup.StartsWith($temporaryBase + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing unsafe quickstart cleanup: $resolvedCleanup"
    }
    if (Test-Path -LiteralPath $resolvedCleanup) {
        Remove-Item -LiteralPath $resolvedCleanup -Recurse -Force
    }
}
