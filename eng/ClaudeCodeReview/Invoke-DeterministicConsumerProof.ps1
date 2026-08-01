[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $ReviewKit,
    [Parameter(Mandatory = $true)] [string] $ConsumerRoot
)

$ErrorActionPreference = 'Stop'
$pkKit = (Resolve-Path -LiteralPath $ReviewKit).Path
$pkConsumer = (Resolve-Path -LiteralPath $ConsumerRoot).Path
$pkManifest = Get-Content -Raw -LiteralPath (Join-Path $pkKit 'manifest.json') | ConvertFrom-Json -Depth 20
if ($pkManifest.supportClaim -ne 'not-evaluated' -or $pkManifest.canonicalDependencyStatus -ne 'rejected') {
    throw 'This deterministic proof expects the current fail-closed Feature 003 support state.'
}
$pkFeed = Join-Path $pkKit 'feed'
$pkTrials = [Collections.Generic.List[object]]::new()
for ($pkOrdinal = 1; $pkOrdinal -le 10; $pkOrdinal++) {
    $pkTrialRoot = Join-Path $pkConsumer ('deterministic-' + $pkOrdinal.ToString('00'))
    $pkToolPath = Join-Path $pkTrialRoot '.program-kit/tools'
    $pkAppData = Join-Path $pkTrialRoot '.program-kit/appdata'
    New-Item -ItemType Directory -Path $pkTrialRoot, (Join-Path $pkAppData 'NuGet') -Force | Out-Null
    $pkConfig = Join-Path $pkTrialRoot 'NuGet.Config'
    $pkEscapedFeed = [Security.SecurityElement]::Escape($pkFeed)
    $pkConfigXml = '<?xml version="1.0" encoding="utf-8"?><configuration><packageSources><clear/><add key="sealed" value="' + $pkEscapedFeed + '"/></packageSources></configuration>'
    Set-Content -LiteralPath $pkConfig -Value $pkConfigXml -Encoding utf8NoBOM
    $pkPriorAppData = $env:APPDATA
    $pkPriorHome = $env:DOTNET_CLI_HOME
    $pkPriorTelemetry = $env:DOTNET_CLI_TELEMETRY_OPTOUT
    $pkPriorNoLogo = $env:DOTNET_NOLOGO
    $pkPriorSkipFirstTime = $env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE
    try {
        $env:APPDATA = $pkAppData
        $env:DOTNET_CLI_HOME = Join-Path $pkTrialRoot '.program-kit/home'
        $env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
        $env:DOTNET_NOLOGO = '1'
        $env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
        dotnet tool install Orbyss.ProgramKit.Cli --tool-path $pkToolPath --version 1.0.0-alpha.1 --configfile $pkConfig --no-cache | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Tool installation failed for deterministic trial $pkOrdinal." }
    }
    finally {
        $env:APPDATA = $pkPriorAppData
        $env:DOTNET_CLI_HOME = $pkPriorHome
        $env:DOTNET_CLI_TELEMETRY_OPTOUT = $pkPriorTelemetry
        $env:DOTNET_NOLOGO = $pkPriorNoLogo
        $env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = $pkPriorSkipFirstTime
    }
    $pkExecutable = Join-Path $pkToolPath $(if ($IsWindows) { 'program-kit.exe' } else { 'program-kit' })
    $pkVersion = & $pkExecutable version --format json | ConvertFrom-Json -Depth 20
    $pkHelp = & $pkExecutable help --format json | ConvertFrom-Json -Depth 20
    if ($pkVersion.utility.cli -ne '1.0.0-alpha.1') { throw "CLI version mismatch in trial $pkOrdinal." }
    if ($pkHelp.utility.sessionAdapterSupport.'anthropic:session-provider:claude-code@2.1.220' -ne 'not-evaluated') { throw "Claude support was upgraded in trial $pkOrdinal." }
    if (Test-Path -LiteralPath (Join-Path $pkTrialRoot '.claude/skills/program-kit/SKILL.md')) { throw "Unauthorized projection effect in trial $pkOrdinal." }
    $pkTrials.Add([ordered]@{
        ordinal = $pkOrdinal
        cliVersion = $pkVersion.utility.cli
        supportClaim = 'not-evaluated'
        effectState = 'none'
        projectionAbsent = $true
    })
}
$pkEvidenceRoot = Join-Path $pkConsumer '.program-kit/evidence'
New-Item -ItemType Directory -Path $pkEvidenceRoot -Force | Out-Null
$pkResult = [ordered]@{
    schema = 'program-kit.claude-code-deterministic-proof/v1'
    reviewKitDigest = $pkManifest.reviewKitDigest
    trials = $pkTrials
    passed = 10
    failed = 0
    supportClaim = 'not-evaluated'
    limitation = 'feature-002-product-acceptance-rejected'
}
$pkResult | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $pkEvidenceRoot 'claude-deterministic-proof.json') -Encoding utf8NoBOM
Write-Output ($pkResult | ConvertTo-Json -Depth 20 -Compress)
