[CmdletBinding()]
param(
    [string]$BaseUrl = 'http://localhost:5000',
    [string]$RoleProbePath = $env:PROGRAMKIT_ROLE_PROBE_PATH
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$suite = Join-Path $PSScriptRoot 'web'
$evidence = Join-Path $repository '.program-kit/evidence/toolchain.json'
python (Join-Path $PSScriptRoot 'toolchain.py') --repository $repository --evidence $evidence
if ($LASTEXITCODE -ne 0) { throw 'Exact managed Node/npm commands are unavailable.' }
$npmRunner = Join-Path $PSScriptRoot 'js_toolchain.py'
Push-Location $suite
try {
    python $npmRunner --repository $repository --evidence $evidence --timeout-seconds 300 npm -- ci --ignore-scripts --strict-peer-deps --engine-strict
    if ($LASTEXITCODE -ne 0) { throw 'Web contract dependency restore failed.' }
    python $npmRunner --repository $repository --evidence $evidence --timeout-seconds 600 npm -- exec -- playwright install --with-deps chromium
    if ($LASTEXITCODE -ne 0) { throw 'Playwright browser installation failed.' }
    $env:PROGRAMKIT_BASE_URL = $BaseUrl
    $env:PROGRAMKIT_ROLE_PROBE_PATH = $RoleProbePath
    $viteConfig = $env:PROGRAMKIT_VITE_CONFIG
    if ($viteConfig) {
        python (Join-Path $suite 'verify_spa_security.py') --vite-config $viteConfig
        if ($LASTEXITCODE -ne 0) { throw 'WEB-V1 SPA serving-security configuration failed.' }
    }
    python $npmRunner --repository $repository --evidence $evidence --timeout-seconds 300 npm -- test
    if ($LASTEXITCODE -ne 0) { throw 'The secure web profile contract failed.' }
}
finally {
    Pop-Location
}
