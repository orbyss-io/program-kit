[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$testsRoot = [System.IO.Path]::GetFullPath((Join-Path $sourceRoot 'tests'))
$testRoot = [System.IO.Path]::GetFullPath((Join-Path $testsRoot '.lifecycle'))

if (-not $testRoot.StartsWith($testsRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Test target escaped the tests directory: $testRoot"
}
if (Test-Path -LiteralPath $testRoot) {
    throw "Refusing to overwrite an existing lifecycle test directory: $testRoot"
}

New-Item -ItemType Directory -Path $testRoot | Out-Null
try {
    Push-Location $testRoot
    specify init . --force --non-interactive --integration codex --ignore-agent-tools `
        --extension (Join-Path $sourceRoot 'extensions\program-kit')
    if ($LASTEXITCODE -ne 0) { throw 'Disposable Spec Kit initialization failed.' }

    specify workflow add (Join-Path $sourceRoot 'workflows\program-kit-bootstrap') --dev
    if ($LASTEXITCODE -ne 0) { throw 'Local workflow installation failed.' }

    $extensionConfig = Get-Content -Raw -LiteralPath '.specify\extensions.yml'
    foreach ($expected in @('after_specify', 'after_plan', 'before_implement', 'after_implement')) {
        if ($extensionConfig -notmatch [regex]::Escape($expected)) {
            throw "Expected hook '$expected' was not registered."
        }
    }

    $installedWorkflow = '.specify\workflows\program-kit-bootstrap\workflow.yml'
    if (-not (Test-Path -LiteralPath $installedWorkflow -PathType Leaf)) {
        throw 'Installed workflow definition was not found.'
    }
    $stepCount = @(Select-String -LiteralPath $installedWorkflow -Pattern '^  - id:').Count
    if ($stepCount -ne 7) {
        throw "Installed workflow exposes $stepCount steps; expected 7."
    }
} finally {
    if ((Get-Location).Path -eq $testRoot) {
        Pop-Location
    }
    $resolvedCleanup = [System.IO.Path]::GetFullPath($testRoot)
    if (-not $resolvedCleanup.StartsWith($testsRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Cleanup target escaped the tests directory: $resolvedCleanup"
    }
    if (Test-Path -LiteralPath $resolvedCleanup) {
        Remove-Item -LiteralPath $resolvedCleanup -Recurse -Force
    }
}

Write-Host 'Local extension/workflow installation and hook checks passed.'
