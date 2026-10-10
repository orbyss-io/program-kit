[CmdletBinding()]
param([switch]$PrepareOnly, [switch]$AuthorizedCodexTask)

$ErrorActionPreference = 'Stop'
function Get-BoundedCommandPath {
    param([System.Collections.IDictionary]$SelectedCommands, [string]$OriginalPath, [string[]]$RequiredDirectories)

    $selectedDirectories = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($source in $SelectedCommands.Values) {
        [void]$selectedDirectories.Add([IO.Path]::GetFullPath((Split-Path -Parent $source)).TrimEnd('\', '/'))
    }
    $includedDirectories = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $directories = [System.Collections.Generic.List[string]]::new()
    # Command parents can contain competing shims. Preserve their original PATH
    # precedence rather than enumerating an unordered command/source dictionary.
    foreach ($entry in ($OriginalPath -split [regex]::Escape([IO.Path]::PathSeparator))) {
        if (-not $entry.Trim()) { continue }
        $directory = [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($entry.Trim().Trim('"'))).TrimEnd('\', '/')
        if ($selectedDirectories.Contains($directory) -and $includedDirectories.Add($directory)) {
            # Get-Command preserves relative/8.3 source spelling. Normalize only
            # for matching; changing the emitted spelling would change Source.
            $directories.Add($entry.Trim().Trim('"'))
        }
    }
    # PowerShell can also discover commands outside PATH. Retain their exact
    # selected parents and the Windows shell/system directories after PATH entries.
    foreach ($directory in (@($SelectedCommands.Values | ForEach-Object { Split-Path -Parent $_ }) + $RequiredDirectories)) {
        $normalizedDirectory = [IO.Path]::GetFullPath($directory).TrimEnd('\', '/')
        if ($includedDirectories.Add($normalizedDirectory)) { $directories.Add($directory) }
    }
    return $directories -join [IO.Path]::PathSeparator
}

$releaseRoot = Split-Path -Parent $PSScriptRoot
$savedLocation = Get-Location
$savedEnvironment = @{}
foreach ($environmentName in @('PATH','PROGRAM_KIT_NPM_TOKEN','NODE_OPTIONS')) {
    $savedEnvironment[$environmentName] = [Environment]::GetEnvironmentVariable($environmentName,'Process')
}
try {
    Set-Location -LiteralPath $releaseRoot
    # Verify the shared device selection. Cached SDK/Node/npm distributions cannot
    # establish readiness. Verify the original selection before any CMD-size repair.
    $uv = Get-Command uv -ErrorAction Stop
    $toolRoot = (& $uv.Source tool dir).Trim()
    $python = Join-Path $toolRoot 'specify-cli/Scripts/python.exe'
    & $python (Join-Path $releaseRoot 'extensions/program-kit-dotnet/templates/dotnet/files/eng/device_toolchain.py') --contributor $releaseRoot
    if ($LASTEXITCODE -ne 0) { throw 'Device readiness failed; complete the printed user-terminal update and refresh the session before retrying.' }
    if ($env:PATH.Length -gt 7000) {
        # npm exec adds project bin folders to PATH. CMD discards overlong PATH
        # values; retain the same active shared executables in a shorter owned
        # process environment. Never select a cached/local replacement.
        $selectedCommands = [ordered]@{}
        foreach ($name in @('node','npm.cmd','dotnet','python','specify','uv','git','docker','gh','codex','pwsh','powershell')) {
            $command = Get-Command $name -ErrorAction SilentlyContinue
            if ($command -and $command.Source) { $selectedCommands[$name] = $command.Source }
        }
        $env:PATH = Get-BoundedCommandPath -SelectedCommands $selectedCommands -OriginalPath $env:PATH `
            -RequiredDirectories @((Join-Path $env:SystemRoot 'System32'), $env:SystemRoot, $PSHOME)
        foreach ($name in $selectedCommands.Keys) {
            if ((Get-Command $name -ErrorAction Stop).Source -ne $selectedCommands[$name]) {
                throw "Active executable selection changed while bounding CMD PATH: $name"
            }
        }
        & $python (Join-Path $releaseRoot 'extensions/program-kit-dotnet/templates/dotnet/files/eng/device_toolchain.py') --contributor $releaseRoot
        if ($LASTEXITCODE -ne 0) { throw 'Shared device selection failed verification after bounding CMD PATH.' }
        Write-Host 'Bounded CMD PATH with identical active executable selections; no outdated tool was masked.'
    }
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
        if ($null -eq $savedEnvironment[$environmentName]) {
            # PowerShell string conversion can turn null into an empty value.
            # Preserve absence explicitly on runtimes that retain empty variables.
            Remove-Item -LiteralPath ('Env:' + $environmentName) -ErrorAction SilentlyContinue
        } else {
            [Environment]::SetEnvironmentVariable($environmentName,$savedEnvironment[$environmentName],'Process')
        }
    }
    Set-Location -LiteralPath $savedLocation.Path
}
