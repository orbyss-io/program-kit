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

$developmentValidators = @(
    'validate_components.py',
    'validate_test_suites.py',
    'validate_orbyss_building_blocks.py',
    'validate_nuget_retirement.py',
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
        Write-Host '  retire_programkit_nuget.py --verify-public (dry run)'
    } else {
        Write-Host '  specify bundle validate --offline'
    }
    return
}

if ($Suite -eq 'Release' -and -not $Approved) {
    throw @'
PROGRAM_KIT_RELEASE_VALIDATION_APPROVAL_REQUIRED

The Release suite is the complete deterministic publication gate and can run for a long time.
Run it only when the user has decided the candidate is ready for publication, then pass -Approved.
During development, omit -Suite Release and run focused validators for the files being changed.
'@
}

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

    foreach ($validator in $validators) {
        Write-Host "Running $Suite validator: $validator"
        & $python (Join-Path $projectRoot "tests\$validator")
        if ($LASTEXITCODE -ne 0) {
            throw "Program Kit validator failed: $validator"
        }
    }

    & $specify.Source bundle validate --path $projectRoot --offline
    if ($LASTEXITCODE -ne 0) {
        throw 'Bundle validation failed.'
    }

    if ($Suite -eq 'Development') {
        Write-Host 'Program Kit development checks passed. Release-only validation was not requested.'
        return
    }

    & $python (Join-Path $projectRoot 'tests\validate_ui_browser.py') --install --install-browser --engines=$BrowserEngines
    if ($LASTEXITCODE -ne 0) {
        throw 'UI browser and analytics acceptance failed.'
    }

    & $python (Join-Path $projectRoot 'scripts\build_release.py')
    if ($LASTEXITCODE -ne 0) {
        throw 'Release build failed.'
    }

    foreach ($validator in @(
        'validate_bootstrap_consistency_e2e.py',
        'validate_packaged_ui.py',
        'validate_release_install.py'
    )) {
        Write-Host "Running packaged Release validator: $validator"
        & $python (Join-Path $projectRoot "tests\$validator")
        if ($LASTEXITCODE -ne 0) {
            throw "Packaged Program Kit validator failed: $validator"
        }
    }

    & $python (Join-Path $projectRoot 'tests\validate_public_upgrade.py') --candidate-dir (Join-Path $projectRoot 'artifacts')
    if ($LASTEXITCODE -ne 0) {
        throw 'Candidate public-upgrade validation failed.'
    }

    & (Join-Path $PSScriptRoot 'Test-LocalInstall.ps1')

    & $python (Join-Path $projectRoot 'scripts\retire_programkit_nuget.py') --verify-public
    if ($LASTEXITCODE -ne 0) {
        throw 'Public component-package verification failed.'
    }

    Write-Host 'Program Kit complete deterministic Release suite passed.'
}
finally {
    if ($transcribing) {
        Stop-Transcript | Out-Null
    }
}
