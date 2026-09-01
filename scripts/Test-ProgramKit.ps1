[CmdletBinding()]
param(
    [switch]$SkipBuild
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

& $python (Join-Path $projectRoot 'tests\validate_components.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Extension or workflow validation failed.'
}

& $python (Join-Path $projectRoot 'tests\validate_governance_state.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Governance-state validation failed.'
}

& $python (Join-Path $projectRoot 'tests\validate_codex_bootstrap.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Codex Desktop bootstrap validation failed.'
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

    & $python (Join-Path $projectRoot 'tests\validate_bootstrap_consistency_e2e.py')
    if ($LASTEXITCODE -ne 0) {
        throw 'Clean-consumer bootstrap consistency validation failed.'
    }

    & $python (Join-Path $projectRoot 'tests\validate_release_install.py')
    if ($LASTEXITCODE -ne 0) {
        throw 'Packaged component and bundle-graph installation test failed.'
    }
}

Write-Host 'Program Kit source checks passed.'
