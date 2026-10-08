[CmdletBinding()]
param([switch]$PrepareOnly, [switch]$AuthorizedCodexTask)

$ErrorActionPreference = 'Stop'
$releaseRoot = Split-Path -Parent $PSScriptRoot
$savedLocation = Get-Location
$savedEnvironment = @{}
foreach ($environmentName in @('PROGRAM_KIT_NPM_TOKEN','NODE_OPTIONS')) {
    $savedEnvironment[$environmentName] = [Environment]::GetEnvironmentVariable($environmentName,'Process')
}
try {
    Set-Location -LiteralPath $releaseRoot
    # Verify the shared device selection. Cached SDK/Node/npm distributions cannot
    # establish readiness and this wrapper never modifies PATH or DOTNET_ROOT.
    $uv = Get-Command uv -ErrorAction Stop
    $toolRoot = (& $uv.Source tool dir).Trim()
    $python = Join-Path $toolRoot 'specify-cli/Scripts/python.exe'
    & $python (Join-Path $releaseRoot 'extensions/program-kit-dotnet/templates/dotnet/files/eng/device_toolchain.py') --contributor $releaseRoot
    if ($LASTEXITCODE -ne 0) { throw 'Device readiness failed; complete the printed user-terminal update and refresh the session before retrying.' }
    if ('--use-system-ca' -notin ($env:NODE_OPTIONS -split '\s+')) {
        $env:NODE_OPTIONS = ($env:NODE_OPTIONS + ' --use-system-ca').Trim()
    }
    Write-Host 'Verified shared device toolchains against authoritative pins.'
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
