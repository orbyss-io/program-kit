[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$testsRoot = [System.IO.Path]::GetFullPath((Join-Path $sourceRoot 'tests'))
$testRoot = [System.IO.Path]::GetFullPath((Join-Path $testsRoot '.lifecycle'))

function Invoke-ProgramKitNative {
    param(
        [Parameter(Mandatory)] [string]$Executable,
        [Parameter(Mandatory)] [object[]]$ArgumentList,
        [Parameter(Mandatory)] [string]$FailureMessage
    )
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
}

function Get-ProgramKitRelativePath {
    param(
        [Parameter(Mandatory)] [string]$RootPath,
        [Parameter(Mandatory)] [string]$CandidatePath
    )

    $rootPrefix = [System.IO.Path]::GetFullPath($RootPath)
    $separator = [System.IO.Path]::DirectorySeparatorChar.ToString()
    if (-not $rootPrefix.EndsWith($separator)) {
        $rootPrefix += $separator
    }
    $candidateFullPath = [System.IO.Path]::GetFullPath($CandidatePath)
    $comparison = if ($env:OS -eq 'Windows_NT') {
        [System.StringComparison]::OrdinalIgnoreCase
    }
    else {
        [System.StringComparison]::Ordinal
    }
    if (-not $candidateFullPath.StartsWith($rootPrefix, $comparison)) {
        throw "Path escaped the expected root: $CandidatePath"
    }
    return $candidateFullPath.Substring($rootPrefix.Length)
}

function Write-ProgramKitUtf8NoBom {
    param(
        [Parameter(Mandatory)] [string]$LiteralPath,
        [Parameter(Mandatory)] [string]$Value
    )

    # Windows PowerShell 5.1's `-Encoding utf8` emits a BOM. Program Kit JSON is
    # canonical UTF-8 without a BOM across PowerShell editions and operating systems.
    $encoding = New-Object System.Text.UTF8Encoding($false)
    $resolvedPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath(
        $LiteralPath
    )
    [System.IO.File]::WriteAllText(
        $resolvedPath,
        $Value + [System.Environment]::NewLine,
        $encoding
    )
}

if (-not $testRoot.StartsWith($testsRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Test target escaped the tests directory: $testRoot"
}
if (Test-Path -LiteralPath $testRoot) {
    throw "Refusing to overwrite an existing lifecycle test directory: $testRoot"
}

New-Item -ItemType Directory -Path $testRoot | Out-Null
$previousConsoleOutputEncoding = [Console]::OutputEncoding
$previousPowerShellOutputEncoding = $OutputEncoding
$previousPythonUtf8 = $env:PYTHONUTF8
$previousPythonIoEncoding = $env:PYTHONIOENCODING
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
try {
    Push-Location $testRoot
    $specifyExecutable = (Get-Command specify -ErrorAction Stop).Source
    $pythonExecutable = (Get-Command python -ErrorAction Stop).Source
    Write-Host "Initializing source-tree disposable consumer: $testRoot"
    Invoke-ProgramKitNative $specifyExecutable @(
        'init', '.', '--force', '--non-interactive', '--integration', 'codex', '--script', 'py',
        '--ignore-agent-tools', '--extension', (Join-Path $sourceRoot 'extensions\program-kit-governance')
    ) 'Disposable Spec Kit initialization failed.'

    Invoke-ProgramKitNative $specifyExecutable @(
        'extension', 'add', (Join-Path $sourceRoot 'extensions\program-kit-dotnet'), '--dev'
    ) 'Local .NET extension installation failed.'

    Invoke-ProgramKitNative $specifyExecutable @(
        'extension', 'add', (Join-Path $sourceRoot 'extensions\program-kit-building-blocks'), '--dev'
    ) 'Local building-block extension installation failed.'

    Invoke-ProgramKitNative $specifyExecutable @(
        'preset', 'add', '--dev', (Join-Path $sourceRoot 'presets\program-kit-governance-preset')
    ) 'Local governance preset installation failed.'

    Invoke-ProgramKitNative $specifyExecutable @(
        'workflow', 'add', (Join-Path $sourceRoot 'workflows\program-kit-bootstrap'), '--dev'
    ) 'Local workflow installation failed.'

    $extensionConfig = Get-Content -Raw -LiteralPath '.specify\extensions.yml'
    foreach ($expected in @('before_constitution', 'before_specify', 'after_specify', 'after_plan', 'after_tasks', 'before_implement', 'after_implement')) {
        if ($extensionConfig -notmatch [regex]::Escape($expected)) {
            throw "Expected hook '$expected' was not registered."
        }
    }

    $installedWorkflow = '.specify\workflows\program-kit-bootstrap\workflow.yml'
    if (-not (Test-Path -LiteralPath $installedWorkflow -PathType Leaf)) {
        throw 'Installed workflow definition was not found.'
    }
    $stepCount = @(Select-String -LiteralPath $installedWorkflow -Pattern '^  - id:').Count
    $sourceWorkflow = Join-Path $sourceRoot 'workflows\program-kit-bootstrap\workflow.yml'
    $expectedStepCount = @(Select-String -LiteralPath $sourceWorkflow -Pattern '^  - id:').Count
    if ($stepCount -ne $expectedStepCount) {
        throw "Installed workflow exposes $stepCount steps; expected $expectedStepCount from source."
    }

    $constitutionSkill = '.agents\skills\speckit-constitution\SKILL.md'
    $pythonResolver = '.specify\scripts\python\resolve_template.py'
    if (-not (Test-Path -LiteralPath $pythonResolver -PathType Leaf)) {
        throw 'Python-flavor Spec Kit resolver was not installed.'
    }
    if ((Get-Content -Raw -LiteralPath $constitutionSkill) -notmatch [regex]::Escape('.specify/scripts/python/resolve_template.py')) {
        throw 'The generated constitution skill does not reference the Python resolver.'
    }

    $validator = '.specify\extensions\program-kit-governance\scripts\governance_state.py'
    if (-not (Test-Path -LiteralPath $validator -PathType Leaf)) {
        throw 'Installed governance-state validator was not found.'
    }
    $codexPreflight = '.specify\extensions\program-kit-governance\scripts\codex_bootstrap_preflight.py'
    if (-not (Test-Path -LiteralPath $codexPreflight -PathType Leaf)) {
        throw 'Installed Codex bootstrap preflight was not found.'
    }
    $bootstrapSkill = '.agents\skills\speckit-program-kit-governance-bootstrap\SKILL.md'
    if (-not (Test-Path -LiteralPath $bootstrapSkill -PathType Leaf)) {
        throw 'Installed Codex-safe bootstrap skill was not found.'
    }
    $c4ViewSkill = '.agents\skills\speckit-program-kit-governance-view-c4\SKILL.md'
    if (-not (Test-Path -LiteralPath $c4ViewSkill -PathType Leaf)) {
        throw 'Installed C4 projection viewing skill was not found.'
    }
    if (-not (Test-Path -LiteralPath '.specify\extensions\program-kit-governance\scripts\c4_view.py' -PathType Leaf)) {
        throw 'Installed C4 projection launcher was not found.'
    }
    # Realistic installed-consumer request: "View the C4 projection."
    $scenarioArchitecture = Join-Path $sourceRoot 'tests\live\scenarios\clean-bootstrap\docs\architecture'
    New-Item -ItemType Directory -Path 'docs\architecture' -Force | Out-Null
    Copy-Item -Path (Join-Path $scenarioArchitecture '*') -Destination 'docs\architecture' -Recurse -Force
    $intakePath = 'docs\architecture\bootstrap-intake.json'
    $draftIntake = Get-Content -Raw -LiteralPath $intakePath | ConvertFrom-Json
    $draftIntake.status = 'draft'
    Write-ProgramKitUtf8NoBom -LiteralPath $intakePath -Value ($draftIntake | ConvertTo-Json -Depth 100)
    $beforeView = @(
        Get-ChildItem -File -Recurse | Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' } | ForEach-Object {
            $relative = Get-ProgramKitRelativePath -RootPath $testRoot -CandidatePath $_.FullName
            "$relative|$((Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash)"
        }
    )
    $c4ViewResult = (& python '.specify\extensions\program-kit-governance\scripts\c4_view.py' inspect --project-root . --json | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "Installed C4 projection inspection failed: $c4ViewResult" }
    $c4ViewPayload = $c4ViewResult | ConvertFrom-Json
    if (-not $c4ViewPayload.projection_current -or -not $c4ViewPayload.projection_parsed `
        -or $c4ViewPayload.intake_status -ne 'draft' `
        -or $c4ViewPayload.review_mode -ne 'draft-intake-review' `
        -or $c4ViewPayload.confirmation_performed `
        -or $c4ViewPayload.architecture_acceptance_performed) {
        throw "Installed C4 projection was not current and parseable: $c4ViewResult"
    }
    $afterView = @(
        Get-ChildItem -File -Recurse | Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' } | ForEach-Object {
            $relative = Get-ProgramKitRelativePath -RootPath $testRoot -CandidatePath $_.FullName
            "$relative|$((Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash)"
        }
    )
    if (Compare-Object -ReferenceObject $beforeView -DifferenceObject $afterView) {
        throw 'Installed view-only C4 inspection changed the consumer repository.'
    }
    $afterReviewIntake = Get-Content -Raw -LiteralPath $intakePath | ConvertFrom-Json
    if ($afterReviewIntake.status -ne 'draft') {
        throw 'Installed view-only C4 inspection confirmed the draft intake.'
    }
    $afterReviewIntake.status = 'confirmed'
    Write-ProgramKitUtf8NoBom -LiteralPath $intakePath -Value ($afterReviewIntake | ConvertTo-Json -Depth 100)
    Invoke-ProgramKitNative $pythonExecutable @(
        '.specify\extensions\program-kit-governance\scripts\bootstrap_intake.py',
        'validate', '--project-root', '.', '--json'
    ) 'Explicitly confirmed intake failed final installed validation.'
    $dotnetSync = '.specify\extensions\program-kit-dotnet\scripts\dotnet_sync.py'
    if (-not (Test-Path -LiteralPath $dotnetSync -PathType Leaf)) {
        throw 'Installed .NET sync extension was not found.'
    }
    $dotnetSkill = '.agents\skills\speckit-program-kit-dotnet-sync\SKILL.md'
    if (-not (Test-Path -LiteralPath $dotnetSkill -PathType Leaf)) {
        throw 'Installed .NET sync skill was not found.'
    }
    $buildingBlocksSync = '.specify\extensions\program-kit-building-blocks\scripts\building_blocks.py'
    if (-not (Test-Path -LiteralPath $buildingBlocksSync -PathType Leaf)) {
        throw 'Installed building-block resolver was not found.'
    }
    $buildingBlocksSkill = '.agents\skills\speckit-program-kit-building-blocks-sync\SKILL.md'
    if (-not (Test-Path -LiteralPath $buildingBlocksSkill -PathType Leaf)) {
        throw 'Installed building-block sync skill was not found.'
    }

    if ($env:CODEX_SESSION_ID -or $env:CODEX_THREAD_ID -or $env:CODEX_INTERNAL_ORIGINATOR_OVERRIDE) {
        $preflightOutput = (& specify workflow run program-kit-bootstrap `
            --input bootstrap_intake=docs/architecture/DOES-NOT-EXIST.json `
            --input integration=codex 2>&1 | Out-String)
        $preflightExitCode = $LASTEXITCODE
        $normalizedPreflightOutput = $preflightOutput -replace '\s+', ' '
        $paused = $preflightExitCode -eq 0 -and $normalizedPreflightOutput -match [regex]::Escape('Status: paused')
        $aborted = $preflightExitCode -ne 0 `
            -and $normalizedPreflightOutput -match [regex]::Escape('Status: aborted') `
            -and $normalizedPreflightOutput -match [regex]::Escape("Gate rejected by user at step 'confirm-agent-boundary-stop'")
        if (-not $paused -and -not $aborted) {
            throw "Codex agent preflight did not stop cleanly: $preflightOutput"
        }
        foreach ($expected in @('confirm-agent-boundary-stop')) {
            if ($normalizedPreflightOutput -notmatch [regex]::Escape($expected)) {
                throw "Workflow-visible Codex preflight stop is missing '$expected': $preflightOutput"
            }
        }
        if ($normalizedPreflightOutput -match '\[intake\]') {
            throw "Codex preflight dispatched intake before stopping: $preflightOutput"
        }
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

Write-Host 'Local extension/workflow installation and hook checks passed.'
