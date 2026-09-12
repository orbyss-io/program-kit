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
$script:releaseReceiptSteps = @()
$script:releaseReceiptStartedAt = [DateTimeOffset]::UtcNow.ToString('o')

function Invoke-ProgramKitNative {
    param(
        [Parameter(Mandatory)]
        [string]$Executable,

        [Parameter(Mandatory)]
        [object[]]$ArgumentList,

        [Parameter(Mandatory)]
        [string]$FailureMessage
    )

    # Windows PowerShell 5.1 promotes any native stderr output to NativeCommandError. With the
    # suite-wide Stop preference, harmless unittest progress on stderr would otherwise abort a
    # successful validator. Merge and replay native output while retaining exit code as authority.
    $stepStartedAt = [DateTimeOffset]::UtcNow.ToString('o')
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $Executable @ArgumentList 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $_.Exception.Message
            }
            else {
                Write-Host $_.ToString()
            }
        }
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($exitCode -ne 0) {
        throw "$FailureMessage (exit code $exitCode)"
    }
    if ($Suite -eq 'Release') {
        $script:releaseReceiptSteps += [ordered]@{
            id = "step-$($script:releaseReceiptSteps.Count + 1)"
            command = @($Executable) + @($ArgumentList | ForEach-Object { $_.ToString() })
            exitCode = 0
            startedAt = $stepStartedAt
            finishedAt = [DateTimeOffset]::UtcNow.ToString('o')
        }
    }
}

$developmentValidators = @(
    'validate_components.py',
    'validate_test_suites.py',
    'validate_specification_intake.py',
    'validate_intake_session.py',
    'validate_intake_authoring.py',
    'validate_json_schema.py',
    'validate_delivery_phase0.py',
    'validate_orbyss_building_blocks.py',
    'validate_building_blocks.py',
    'validate_architecture_placement.py',
    'validate_bootstrap_lifecycle.py',
    'validate_building_block_availability.py',
    'validate_legacy_programkit_nuget.py',
    'validate_generated_contract_schemas.py'
)
$releaseOnlyValidators = @(
    'validate_ui_experience.py',
    'validate_governance_state.py',
    'validate_local_upgrade.py',
    'validate_bootstrap_context.py',
    'validate_bootstrap_intake.py',
    'validate_bootstrap_semantics.py',
    'validate_c4_view.py',
    'validate_live_bootstrap_acceptance.py',
    'validate_lifecycle_profiles.py',
    'validate_js_toolchain.py',
    'validate_dotnet_scaffold.py',
    'validate_dotnet_build_contract.py',
    'validate_dotnet_test_discovery.py',
    'validate_repository_verification_hook.py',
    'validate_codex_bootstrap.py'
)
$validators = if ($Suite -eq 'Release') {
    @($developmentValidators + $releaseOnlyValidators)
} else {
    @($developmentValidators)
}

if ($List) {
    Write-Host "$Suite validators:"
    $validators | ForEach-Object { Write-Host "  $_" }
    if ($Suite -eq 'Release') {
        Write-Host '  validate_ui_browser.py'
        Write-Host '  specify bundle validate'
        Write-Host '  build_release.py'
        Write-Host '  validate_bootstrap_consistency_e2e.py'
        Write-Host '  validate_packaged_ui.py'
        Write-Host '  validate_release_install.py'
        Write-Host '  validate_public_upgrade.py --candidate-dir artifacts'
        Write-Host '  Test-LocalInstall.ps1'
        Write-Host '  public_availability.py --all'
        Write-Host '  verify_legacy_programkit_nuget.py --verify-public (read-only)'
        Write-Host '  write_release_receipt.py'
    } else {
        Write-Host '  specify bundle validate --offline'
    }
    return
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

if ($Suite -eq 'Release' -and -not $Approved) {
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
if ($Suite -eq 'Release') {
    if (-not $EvidencePath) {
        $version = (Get-Content -Raw -LiteralPath (Join-Path $projectRoot 'VERSION')).Trim()
        $EvidencePath = Join-Path $projectRoot "artifacts\release-validation-$version.log"
    }
    $EvidencePath = [System.IO.Path]::GetFullPath($EvidencePath)
    New-Item -ItemType Directory -Force -Path ([System.IO.Path]::GetDirectoryName($EvidencePath)) | Out-Null
    Start-Transcript -LiteralPath $EvidencePath -Force | Out-Null
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

    foreach ($validator in $validators) {
        Write-Host "Running $Suite validator: $validator"
        Invoke-ProgramKitNative $python @((Join-Path $projectRoot "tests\$validator")) "Program Kit validator failed: $validator"
    }

    Invoke-ProgramKitNative $specify.Source @('bundle', 'validate', '--path', $projectRoot, '--offline') 'Bundle validation failed.'

    if ($Suite -eq 'Development') {
        Write-Host 'Program Kit development checks passed. Release-only validation was not requested.'
        return
    }

    Invoke-ProgramKitNative $python @(
        (Join-Path $projectRoot 'tests\validate_ui_browser.py'),
        '--install',
        '--install-browser',
        "--engines=$BrowserEngines"
    ) 'UI browser and analytics acceptance failed.'

    Invoke-ProgramKitNative $python @((Join-Path $projectRoot 'scripts\build_release.py')) 'Release build failed.'

    foreach ($validator in @(
        'validate_bootstrap_consistency_e2e.py',
        'validate_packaged_ui.py',
        'validate_release_install.py'
    )) {
        Write-Host "Running packaged Release validator: $validator"
        Invoke-ProgramKitNative $python @((Join-Path $projectRoot "tests\$validator")) "Packaged Program Kit validator failed: $validator"
    }

    Invoke-ProgramKitNative $python @(
        (Join-Path $projectRoot 'tests\validate_public_upgrade.py'),
        '--candidate-dir',
        (Join-Path $projectRoot 'artifacts')
    ) 'Candidate public-upgrade validation failed.'

    Write-Host 'Running source-tree installation validator: Test-LocalInstall.ps1'
    $localInstallStartedAt = [DateTimeOffset]::UtcNow.ToString('o')
    & (Join-Path $PSScriptRoot 'Test-LocalInstall.ps1')
    $script:releaseReceiptSteps += [ordered]@{
        id = "step-$($script:releaseReceiptSteps.Count + 1)"
        command = @((Join-Path $PSScriptRoot 'Test-LocalInstall.ps1'))
        exitCode = 0
        startedAt = $localInstallStartedAt
        finishedAt = [DateTimeOffset]::UtcNow.ToString('o')
    }

    Invoke-ProgramKitNative $python @(
        (Join-Path $projectRoot 'extensions/program-kit-building-blocks/scripts/public_availability.py'),
        '--target',
        $projectRoot,
        '--catalog',
        (Join-Path $projectRoot 'extensions/program-kit-building-blocks/references/orbyss-building-blocks.json'),
        '--all',
        '--evidence',
        'artifacts/building-block-public-availability.json'
    ) 'Catalog-wide NuGet, npm, and host-image public availability failed.'

    Invoke-ProgramKitNative $python @(
        (Join-Path $projectRoot 'scripts\verify_legacy_programkit_nuget.py'),
        '--verify-public'
    ) 'Read-only legacy package compatibility verification failed.'

    $receiptJournal = Join-Path $projectRoot 'artifacts\release-validation-steps.json'
    $receiptJournalJson = $script:releaseReceiptSteps | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($receiptJournal, $receiptJournalJson, $utf8NoBom)
    try {
        Invoke-ProgramKitNative $python @(
            (Join-Path $projectRoot 'scripts\write_release_receipt.py'),
            '--root',
            $projectRoot,
            '--journal',
            $receiptJournal,
            '--browser-engines',
            $BrowserEngines,
            '--started-at',
            $script:releaseReceiptStartedAt
        ) 'Release receipt generation failed.'
    }
    finally {
        Remove-Item -LiteralPath $receiptJournal -Force -ErrorAction SilentlyContinue
    }
    Write-Host 'Program Kit complete deterministic Release suite passed.'
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
