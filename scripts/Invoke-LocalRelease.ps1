[CmdletBinding()]
param([switch]$PrepareOnly, [switch]$AuthorizedCodexTask)

$ErrorActionPreference = 'Stop'
$releaseRoot = Split-Path -Parent $PSScriptRoot
$releaseTemplate = Join-Path $releaseRoot 'extensions/program-kit-dotnet/templates/dotnet/files'
$releaseNodeVersion = (Get-Content -Raw -LiteralPath (Join-Path $releaseTemplate '.nvmrc')).Trim().TrimStart('v')
$releaseNpmVersion = (Get-Content -Raw -LiteralPath (Join-Path $releaseTemplate '.npm-version')).Trim()
$releaseNode = Join-Path $releaseRoot "artifacts\toolchains\node-v$releaseNodeVersion-win-x64"
$releaseDotnet = Join-Path $releaseRoot 'artifacts\toolchains\dotnet'
$releaseNpm = Join-Path $releaseNode 'npm.cmd'
$savedLocation = Get-Location
$savedEnvironment = @{}
foreach ($environmentName in @('PATH','DOTNET_ROOT','PROGRAMKIT_NODE_EXECUTABLE','PROGRAMKIT_NPM_EXECUTABLE','PLAYWRIGHT_BROWSERS_PATH','PROGRAM_KIT_NPM_TOKEN','NODE_OPTIONS')) {
    $savedEnvironment[$environmentName] = [Environment]::GetEnvironmentVariable($environmentName,'Process')
}
try {
    Set-Location -LiteralPath $releaseRoot
    # Native npm uses cmd.exe, whose PATH expansion fails beyond its command
    # length limit. Keep the owned validation process tree's PATH bounded.
    $releasePathDirectories = @($releaseNode,$releaseDotnet)
    foreach ($releaseTool in @('specify','uv','git','python','docker','gh','pwsh','powershell')) {
        $releaseCommand = Get-Command $releaseTool -ErrorAction Stop
        $releasePathDirectories += Split-Path -Parent $releaseCommand.Source
    }
    $releasePathDirectories += @((Join-Path $env:SystemRoot 'System32'),$env:SystemRoot,$PSHOME)
    $env:PATH = ($releasePathDirectories | Select-Object -Unique) -join ';'
    $env:DOTNET_ROOT = $releaseDotnet
    $env:PROGRAMKIT_NODE_EXECUTABLE = Join-Path $releaseNode 'node.exe'
    $env:PROGRAMKIT_NPM_EXECUTABLE = $releaseNpm
    if ('--use-system-ca' -notin ($env:NODE_OPTIONS -split '\s+')) {
        $env:NODE_OPTIONS = ($env:NODE_OPTIONS + ' --use-system-ca').Trim()
    }
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $releaseRoot 'artifacts\toolchains\playwright-browsers'
    if ((& node --version) -ne "v$releaseNodeVersion") { throw "Cached Node $releaseNodeVersion is unavailable." }
    $releaseSdkVersion = (Get-Content -Raw -LiteralPath (Join-Path $releaseRoot 'extensions/program-kit-dotnet/templates/dotnet/files/global.json') | ConvertFrom-Json).sdk.version
    if ((& dotnet --version) -ne $releaseSdkVersion) { throw "Cached .NET SDK $releaseSdkVersion is unavailable. Prepare the selected exact SDK before release." }
    if ((& $releaseNpm --version) -ne $releaseNpmVersion) { throw "Cached npm $releaseNpmVersion is unavailable." }
    Write-Host "Verified cached toolchains: Node $releaseNodeVersion, npm $releaseNpmVersion, .NET SDK $releaseSdkVersion."
    if ($PrepareOnly) { return }
    # Fail before the full suite if its real database/host fixtures cannot run.
    $releaseContainerOs = ''
    try { $releaseContainerOs = (& docker info --format '{{.OSType}}' 2>$null).Trim() } catch { }
    if ($LASTEXITCODE -ne 0 -or $releaseContainerOs -ne 'linux') {
        throw 'PROGRAM_KIT_RELEASE_DOCKER_UNAVAILABLE: Start Docker Desktop with the Linux engine, wait until it is ready, then retry this command. The Release suite has not started.'
    }
    Write-Host 'Verified Docker Linux engine for real database and published-host checks.'
    if (-not $env:PROGRAM_KIT_NPM_TOKEN) {
        $env:PROGRAM_KIT_NPM_TOKEN = (& gh auth token --hostname github.com).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $env:PROGRAM_KIT_NPM_TOKEN) { throw 'GitHub login did not provide a package token.' }
    }
    & (Join-Path $releaseRoot 'scripts\Test-ProgramKit.ps1') -Suite Release -Approved -BrowserEngines 'chromium,webkit' -AuthorizedCodexTask:$AuthorizedCodexTask
}
finally {
    foreach ($environmentName in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($environmentName,$savedEnvironment[$environmentName],'Process')
    }
    Set-Location -LiteralPath $savedLocation.Path
}
