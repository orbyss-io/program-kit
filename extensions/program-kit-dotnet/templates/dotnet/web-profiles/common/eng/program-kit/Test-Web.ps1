[CmdletBinding()]
param(
    [string]$BaseUrl = 'http://localhost:5000',
    [string]$RoleProbePath = $env:PROGRAMKIT_ROLE_PROBE_PATH
)

$ErrorActionPreference = 'Stop'
$suite = Join-Path $PSScriptRoot 'web'
Push-Location $suite
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'Web contract dependency restore failed.' }
    npx playwright install --with-deps chromium
    if ($LASTEXITCODE -ne 0) { throw 'Playwright browser installation failed.' }
    $env:PROGRAMKIT_BASE_URL = $BaseUrl
    $env:PROGRAMKIT_ROLE_PROBE_PATH = $RoleProbePath
    $viteConfig = $env:PROGRAMKIT_VITE_CONFIG
    if ($viteConfig) {
        python (Join-Path $suite 'verify_spa_security.py') --vite-config $viteConfig
        if ($LASTEXITCODE -ne 0) { throw 'WEB-V1 SPA serving-security configuration failed.' }
    }
    npm test
    if ($LASTEXITCODE -ne 0) { throw 'The secure web profile contract failed.' }
}
finally {
    Pop-Location
}
