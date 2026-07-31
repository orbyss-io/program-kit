[CmdletBinding()]
param(
    [switch] $PlanOnly
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = [IO.Path]::GetFullPath(
    (Join-Path $PSScriptRoot '..'))
$solutionPath = Join-Path $repositoryRoot 'ProgramKit.sln'
$unitProject = Join-Path `
    $repositoryRoot `
    'tests/Orbyss.ProgramKit.UnitTests/Orbyss.ProgramKit.UnitTests.csproj'
$gatePlan = Join-Path $PSScriptRoot 'Invoke-CSharpGateTestPlan.ps1'
$profile = [ordered]@{
    identity = 'pkid:profile:program-kit:private-csharp-gate-exhaustive'
    version = '1.0.1'
    digest = 'sha256:2e383f220030e2933dca3e7af27543e73a28451506c183538d6d84aba689791f'
}
$plan = [ordered]@{
    planVersion = '0.1.0-alpha.1'
    profile = $profile
    invocations = @(
        [ordered]@{
            phase = 'locked-restore'
            executable = 'dotnet'
            arguments = @(
                'restore',
                $solutionPath,
                '--configfile',
                (Join-Path $repositoryRoot 'NuGet.Config'),
                '--locked-mode')
        },
        [ordered]@{
            phase = 'unit-tests'
            executable = 'dotnet'
            arguments = @(
                'test',
                $unitProject,
                '--configuration',
                'Release',
                '--no-restore',
                '--minimum-expected-tests',
                '1')
        },
        [ordered]@{
            phase = 'private-gate'
            executable = 'pwsh'
            arguments = @(
                '-NoProfile',
                '-File',
                $gatePlan,
                '-Profile',
                'Exhaustive')
        })
}

if ($PlanOnly) {
    $plan | ConvertTo-Json -Depth 8
    return
}

foreach ($invocation in $plan.invocations) {
    & $invocation.executable @($invocation.arguments)
    if ($LASTEXITCODE -ne 0) {
        throw "Program Kit integration phase '$($invocation.phase)' failed with exit code $LASTEXITCODE."
    }
}

Write-Output (
    "Program Kit integration passed: profile=$(
        $profile.identity)@$($profile.version) digest=$($profile.digest)")
