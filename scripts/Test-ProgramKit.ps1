[CmdletBinding()]
param(
    [switch]$SkipBuild,
    [string]$BrowserEngines = 'chromium,firefox,webkit'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

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

$validators = @(
    'validate_components.py',
    'validate_ui_experience.py',
    'validate_orbyss_building_blocks.py',
    'validate_nuget_retirement.py',
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
    'validate_generated_contract_schemas.py',
    'validate_codex_bootstrap.py'
)
foreach ($validator in $validators) {
    & $python (Join-Path $projectRoot "tests\$validator")
    if ($LASTEXITCODE -ne 0) {
        throw "Program Kit validator failed: $validator"
    }
}

& $python (Join-Path $projectRoot 'tests\validate_ui_browser.py') --install --install-browser --engines=$BrowserEngines
if ($LASTEXITCODE -ne 0) {
    throw 'UI browser and analytics acceptance failed.'
}

& $specify.Source bundle validate --path $projectRoot --offline
if ($LASTEXITCODE -ne 0) {
    throw 'Bundle validation failed.'
}

if (-not $SkipBuild) {
    & $python (Join-Path $projectRoot 'scripts\build_release.py')
    if ($LASTEXITCODE -ne 0) {
        throw 'Release build failed.'
    }

    foreach ($validator in @(
        'validate_bootstrap_consistency_e2e.py',
        'validate_packaged_ui.py',
        'validate_release_install.py'
    )) {
        & $python (Join-Path $projectRoot "tests\$validator")
        if ($LASTEXITCODE -ne 0) {
            throw "Packaged Program Kit validator failed: $validator"
        }
    }
}

Write-Host 'Program Kit AI-extension checks passed.'
