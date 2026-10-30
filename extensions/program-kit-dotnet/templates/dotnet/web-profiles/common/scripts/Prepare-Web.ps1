[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
Import-Module (Join-Path $PSScriptRoot 'ProgramKitPython.psm1') -Force
$python = Resolve-ProgramKitPython -Repository $repository
$previousPython = $env:SPECKIT_PYTHON
$previousBrowsers = $env:PLAYWRIGHT_BROWSERS_PATH
try {
    $env:SPECKIT_PYTHON = $python
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $repository 'artifacts/cache/playwright-browsers'
    $evidence = Join-Path $repository 'artifacts/program-kit/toolchain.json'
    & $python (Join-Path $PSScriptRoot 'toolchain.py') --repository $repository --evidence $evidence
    if ($LASTEXITCODE -ne 0) { throw 'Exact device toolchain is unavailable; follow the reported user-owned recovery.' }
    Push-Location (Join-Path $PSScriptRoot 'web')
    try {
        $runner = Join-Path $PSScriptRoot 'js_toolchain.py'
        & $python $runner --repository $repository --evidence $evidence --timeout-seconds 300 npm -- ci --ignore-scripts --strict-peer-deps --engine-strict
        if ($LASTEXITCODE -ne 0) { throw 'Explicit web dependency preparation failed.' }
        & $python $runner --repository $repository --evidence $evidence --timeout-seconds 600 npm -- exec --no -- playwright install chromium
        if ($LASTEXITCODE -ne 0) { throw 'Explicit Chromium preparation failed; required OS prerequisites belong to device preparation.' }
        & $python (Join-Path $PSScriptRoot 'web_readiness.py') --repository $repository --evidence $evidence
        if ($LASTEXITCODE -ne 0) { throw 'Prepared web runtime did not pass read-only admission.' }
    }
    finally { Pop-Location }
}
finally {
    $env:SPECKIT_PYTHON = $previousPython
    $env:PLAYWRIGHT_BROWSERS_PATH = $previousBrowsers
}
