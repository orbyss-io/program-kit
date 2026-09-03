[CmdletBinding()]
param(
    [string]$BaseUrl = 'http://localhost:5000',
    [string]$PermissionProbePath = $env:PROGRAMKIT_PERMISSION_PROBE_PATH,
    [string]$SpaUrl = $env:PROGRAMKIT_SPA_URL,
    [string]$SpaLoginPath = $env:PROGRAMKIT_SPA_LOGIN_PATH,
    [string]$ViteConfig = $env:PROGRAMKIT_VITE_CONFIG
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
    $env:PROGRAMKIT_PERMISSION_PROBE_PATH = $PermissionProbePath
    $env:PROGRAMKIT_SPA_URL = $SpaUrl
    $env:PROGRAMKIT_SPA_LOGIN_PATH = $SpaLoginPath
    $env:PROGRAMKIT_VITE_CONFIG = $ViteConfig
    $spaVerifier = Join-Path $PSScriptRoot 'verify_spa_profile.py'
    if (Test-Path -LiteralPath $spaVerifier -PathType Leaf) {
        python $spaVerifier --repository $repository
        if ($LASTEXITCODE -ne 0) { throw 'The synchronized SPA-PKCE profile is invalid.' }
    }
    if ($ViteConfig) {
        python (Join-Path $suite 'verify_spa_security.py') --vite-config $ViteConfig
        if ($LASTEXITCODE -ne 0) { throw 'WEB-V1 SPA serving-security configuration failed.' }
    }
    python $npmRunner --repository $repository --evidence $evidence --timeout-seconds 300 npm -- test
    if ($LASTEXITCODE -ne 0) { throw 'The secure web profile contract failed.' }
}
finally {
    Pop-Location
}
