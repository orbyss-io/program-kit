param(
    [ValidateSet('Auto', 'Exhaustive')]
    [string] $Profile = 'Auto',

    [string] $BaseRevision,

    [switch] $PlanOnly
)

$ErrorActionPreference = 'Stop'

$programKitRoot = Split-Path -Parent $PSScriptRoot
$repositoryRoot = $programKitRoot
$conformanceProject = Join-Path `
    $programKitRoot `
    'tests/Orbyss.ProgramKit.ConformanceTests/Orbyss.ProgramKit.ConformanceTests.csproj'

function Test-GateSensitivePath {
    param(
        [Parameter(Mandatory)]
        [string] $Path
    )

    $normalized = $Path.Replace('\', '/')
    return (
        $normalized -eq 'global.json' -or
        $normalized -eq 'Directory.Build.props' -or
        $normalized -eq 'Directory.Build.targets' -or
        $normalized -eq 'Directory.Packages.props' -or
        $normalized -eq 'NuGet.Config' -or
        $normalized -eq 'ProgramKit.sln' -or
        $normalized -eq 'build/Invoke-CSharpGateTestPlan.ps1' -or
        $normalized -eq 'governance/approved-warning-suppressions.tsv' -or
        $normalized.StartsWith(
            'tools/Orbyss.ProgramKit.CSharpGate/',
            [StringComparison]::Ordinal) -or
        $normalized.StartsWith(
            'tests/Orbyss.ProgramKit.ConformanceTests/Build/CSharpGate',
            [StringComparison]::Ordinal) -or
        $normalized.StartsWith(
            'tests/Orbyss.ProgramKit.ConformanceTests/Fixtures/CSharpGate/',
            [StringComparison]::Ordinal) -or
        $normalized -eq 'tests/Orbyss.ProgramKit.ConformanceTests/Orbyss.ProgramKit.ConformanceTests.csproj' -or
        $normalized -eq 'tests/Orbyss.ProgramKit.ConformanceTests/packages.lock.json' -or
        $normalized -eq 'tests/Orbyss.ProgramKit.UnitTests/Orbyss.ProgramKit.UnitTests.csproj' -or
        $normalized -eq 'tests/Orbyss.ProgramKit.UnitTests/packages.lock.json' -or
        $normalized -eq 'src/Orbyss.ProgramKit.Tasks.Schedules.Cronos/Orbyss.ProgramKit.Tasks.Schedules.Cronos.csproj' -or
        $normalized -eq 'src/Orbyss.ProgramKit.Tasks.Schedules.Cronos/packages.lock.json' -or
        $normalized -eq 'fixtures/observatory-scheduling/tests/ObservatoryScheduling.Tests/ObservatoryScheduling.Tests.csproj' -or
        $normalized -eq 'fixtures/observatory-scheduling/tests/ObservatoryScheduling.Tests/packages.lock.json'
    )
}

function Get-ChangedRepositoryPath {
    if ([string]::IsNullOrWhiteSpace($BaseRevision)) {
        $tracked = & git -C $repositoryRoot diff --name-only --diff-filter=ACMRTUXB HEAD --
    }
    else {
        $committed = & git -C $repositoryRoot diff --name-only --diff-filter=ACMRTUXB "$BaseRevision...HEAD" --
        if ($LASTEXITCODE -ne 0) {
            throw 'Unable to inspect committed repository changes.'
        }
        $working = & git -C $repositoryRoot diff --name-only --diff-filter=ACMRTUXB HEAD --
        $tracked = @($committed) + @($working)
    }
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to inspect tracked repository changes.'
    }

    $untracked = & git -C $repositoryRoot ls-files --others --exclude-standard --
    if ($LASTEXITCODE -ne 0) {
        throw 'Unable to inspect untracked repository changes.'
    }

    return @($tracked) + @($untracked) |
        Sort-Object -Unique
}

function Invoke-ConformanceSlice {
    param(
        [Parameter(Mandatory)]
        [string] $Filter,

        [switch] $NoBuild
    )

    $arguments = @(
        'test',
        $conformanceProject,
        '--no-restore',
        '--filter',
        $Filter,
        '--verbosity',
        'minimal'
    )
    if ($NoBuild) {
        $arguments = @(
            'test',
            $conformanceProject,
            '--no-build',
            '--no-restore',
            '--filter',
            $Filter,
            '--verbosity',
            'minimal'
        )
    }

    & dotnet @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "C# gate conformance slice failed with exit code $LASTEXITCODE."
    }
}

$changedPaths = @(Get-ChangedRepositoryPath)
$gateSensitivePaths = @(
    $changedPaths |
        Where-Object { Test-GateSensitivePath -Path $_ }
)
$ciWithoutBaseRevision = (
    $env:CI -eq 'true' -and
    [string]::IsNullOrWhiteSpace($BaseRevision)
)
$runExhaustive = (
    $Profile -eq 'Exhaustive' -or
    $gateSensitivePaths.Count -gt 0 -or
    $ciWithoutBaseRevision
)

Write-Output "C# gate test profile: $(
    if ($runExhaustive) { 'exhaustive' } else { 'routine' }
)"
if ($gateSensitivePaths.Count -gt 0) {
    Write-Output 'Gate-sensitive changes:'
    $gateSensitivePaths | ForEach-Object { Write-Output "  $_" }
}
if ($ciWithoutBaseRevision) {
    Write-Output 'CI supplied no base revision; Auto failed closed to exhaustive.'
}

if ($PlanOnly) {
    return
}

Invoke-ConformanceSlice `
    -Filter 'TestCategory!=ProgramKitGateExhaustive'

if ($runExhaustive) {
    Invoke-ConformanceSlice `
        -Filter 'TestCategory=ProgramKitGateExhaustive' `
        -NoBuild
}
