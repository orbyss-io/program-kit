[CmdletBinding()]
param(
    [ValidateSet('Development', 'Release')]
    [string]$Suite = 'Development',

    [switch]$Approved,

    [switch]$List,

    [string]$BrowserEngines = 'chromium,firefox,webkit',

    [string]$EvidencePath = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
function Invoke-ProgramKitNative {
    param([string]$Executable, [object[]]$ArgumentList, [string]$FailureMessage)
    & $Executable @ArgumentList
    if ($LASTEXITCODE -ne 0) { throw $FailureMessage }
}

if ($Suite -eq 'Release' -and $Host.Name -eq 'Windows PowerShell ISE Host') {
    throw @'
PROGRAM_KIT_RELEASE_VALIDATION_ISE_UNSUPPORTED

Do not run the complete Release suite in Windows PowerShell ISE. Long-running native-process
validation can terminate the ISE host without allowing the transcript or cleanup blocks to finish.
Open a standalone Windows PowerShell console or a Windows Terminal Windows PowerShell profile, then
run the approved Release command there.
'@
}

if ($Suite -eq 'Release' -and -not $Approved -and -not $List) {
    throw @'
PROGRAM_KIT_RELEASE_VALIDATION_APPROVAL_REQUIRED

The Release suite is the complete deterministic publication gate and can run for a long time.
Run it only when the user has decided the candidate is ready for publication, then pass -Approved.
During development, omit -Suite Release and run focused validators for the files being changed.
'@
}

$previousConsoleOutputEncoding = [Console]::OutputEncoding
$previousPowerShellOutputEncoding = $OutputEncoding
$previousPythonUtf8 = $env:PYTHONUTF8
$previousPythonIoEncoding = $env:PYTHONIOENCODING
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

$transcribing = $false
if ($Suite -eq 'Release' -and -not $List) {
    if (-not $EvidencePath) {
        $version = (Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'VERSION')).Trim()
        $EvidencePath = Join-Path $projectRoot "artifacts\release-validation-$version.log"
    }
    $EvidencePath = [System.IO.Path]::GetFullPath($EvidencePath)
    New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($EvidencePath)) | Out-Null
    if (Test-Path -LiteralPath $EvidencePath) {
        $archivePath = $EvidencePath + '.' + [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfff') + '.previous'
        Move-Item -LiteralPath $EvidencePath -Destination $archivePath
    }
    Start-Transcript -LiteralPath $EvidencePath | Out-Null
    $transcribing = $true
    Write-Host "Release validation evidence: $EvidencePath"
}

try {
    $specify = Get-Command specify -ErrorAction Stop
    $uv = Get-Command uv -ErrorAction Stop
    $toolRoot = (& $uv.Source tool dir).Trim()

    if ($IsWindows -or $env:OS -eq 'Windows_NT') {
        $python = Join-Path $toolRoot 'specify-cli\Scripts\python.exe'
    } else {
        $python = Join-Path $toolRoot 'specify-cli/bin/python'
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        throw "Could not locate the specify-cli Python environment at $python"
    }

    Invoke-ProgramKitNative $python @(
        (Join-Path $projectRoot 'extensions/program-kit-governance/scripts/schema_runtime.py'),
        'setup', '--offline'
    ) 'Prepare the JSON Schema runtime for the suite interpreter using the command above; validation never downloads dependencies.'

    $arguments = @((Join-Path $projectRoot 'scripts/run_validation.py'), '--suite', $Suite, "--engines=$BrowserEngines")
    if ($List) { $arguments += '--list' }
    if ($Approved) { $arguments += '--approved' }
    if ($Suite -eq 'Release' -and -not $List) { $arguments += '--receipt' }
    & $python @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Program Kit validation failed. Inspect the preserved per-check journal and logs.' }

}
finally {
    if ($transcribing) {
        Stop-Transcript | Out-Null
    }
    [Console]::OutputEncoding = $previousConsoleOutputEncoding
    $OutputEncoding = $previousPowerShellOutputEncoding
    if ($null -eq $previousPythonUtf8) {
        Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONUTF8 = $previousPythonUtf8
    }
    if ($null -eq $previousPythonIoEncoding) {
        Remove-Item Env:PYTHONIOENCODING -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONIOENCODING = $previousPythonIoEncoding
    }
}
