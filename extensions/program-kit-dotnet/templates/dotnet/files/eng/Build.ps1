[CmdletBinding()]
param(
    [switch]$SkipTests,
    [Alias('SkipBundle')]
    [switch]$SkipReleaseBundle,
    [switch]$LockedMode,
    [switch]$InitializeOpenApiBaseline,
    [switch]$UpdateOpenApiArtifact,
    [switch]$VerifyArchitecture,
    [string[]]$RootPackage = @()
)

$ErrorActionPreference = 'Stop'
$root = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$version = (Get-Content -Raw -LiteralPath (Join-Path $root 'VERSION')).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+([-.][0-9A-Za-z.-]+)?$') {
    throw "VERSION is not a valid SemVer value: '$version'"
}

$solutions = @(Get-ChildItem -LiteralPath $root -File | Where-Object { $_.Extension -in '.sln', '.slnx' })
if ($solutions.Count -ne 1) {
    throw "Expected exactly one solution in $root; found $($solutions.Count)."
}

function Invoke-ProgramKitDotNetCapture {
    param(
        [Parameter(Mandatory)]
        [object[]]$ArgumentList
    )

    # Windows PowerShell 5.1 promotes native stderr to NativeCommandError. Capture
    # diagnostics without letting that compatibility behavior preempt the exit-code
    # checks that define this build contract.
    $previousPreference = $ErrorActionPreference
    $exitCode = $null
    try {
        $ErrorActionPreference = 'Continue'
        $nativeOutput = @(& dotnet @ArgumentList 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($null -eq $exitCode) {
        $exitCode = 1
    }
    $normalizedOutput = @(
        $nativeOutput | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                $_.Exception.Message
            }
            else {
                $_.ToString()
            }
        }
    )
    return [PSCustomObject]@{
        ExitCode = $exitCode
        Output = $normalizedOutput
    }
}

function Get-TestProjectCount {
    param(
        [Parameter(Mandatory)]
        [string]$SolutionPath
    )

    $solutionDirectory = Split-Path -Parent $SolutionPath
    $solutionProjectsResult = Invoke-ProgramKitDotNetCapture -ArgumentList @(
        'sln', $SolutionPath, 'list'
    )
    $solutionProjectsOutput = @($solutionProjectsResult.Output)
    if ($solutionProjectsResult.ExitCode -ne 0) {
        $solutionProjectsOutput | ForEach-Object { Write-Host $_ }
        throw "Could not enumerate projects in solution $SolutionPath."
    }

    $projectPaths = @(
        $solutionProjectsOutput |
            ForEach-Object { ([string]$_).Trim() } |
            Where-Object { $_ -match '(?i)\.(csproj|fsproj|vbproj)$' } |
            ForEach-Object {
                if ([System.IO.Path]::IsPathRooted($_)) {
                    [System.IO.Path]::GetFullPath($_)
                }
                else {
                    [System.IO.Path]::GetFullPath((Join-Path $solutionDirectory $_))
                }
            }
    )

    $testProjectCount = 0
    foreach ($projectPath in $projectPaths) {
        if (-not (Test-Path -LiteralPath $projectPath -PathType Leaf)) {
            throw "Solution project does not exist: $projectPath"
        }

        $testPropertyResult = Invoke-ProgramKitDotNetCapture -ArgumentList @(
            'msbuild', $projectPath, '-nologo', '-verbosity:quiet',
            '-getProperty:IsTestProject'
        )
        $testPropertyOutput = @($testPropertyResult.Output)
        if ($testPropertyResult.ExitCode -ne 0) {
            $testPropertyOutput | ForEach-Object { Write-Host $_ }
            throw "Could not evaluate IsTestProject for $projectPath."
        }

        $testProperty = ($testPropertyOutput -join "`n").Trim()
        if ([string]::IsNullOrWhiteSpace($testProperty)) {
            continue
        }

        $isTestProject = $false
        if (-not [bool]::TryParse($testProperty, [ref]$isTestProject)) {
            throw "IsTestProject for $projectPath is not a Boolean value: '$testProperty'"
        }
        if ($isTestProject) {
            $testProjectCount++
        }
    }

    return $testProjectCount
}

$artifacts = Join-Path $root 'artifacts'
$packageVersionRoot = Join-Path (Join-Path $artifacts 'packages') $version
# A pack invocation owns its inventory. Earlier outputs (including packages from
# removed projects) remain historical evidence and cannot enter the new bundle.
$packages = Join-Path $packageVersionRoot ([Guid]::NewGuid().ToString('N'))
$openApiRegistry = Join-Path $root 'eng/openapi-contracts.json'
$openApiEnabled = $false
if (Test-Path -LiteralPath $openApiRegistry) {
    $openApiConfiguration = Get-Content -Raw -LiteralPath $openApiRegistry | ConvertFrom-Json
    if ($openApiConfiguration.schemaVersion -ne 1 -or $null -eq $openApiConfiguration.contracts) {
        throw 'OpenAPI registry must use schemaVersion 1 and declare a contracts array.'
    }
    $openApiEnabled = @($openApiConfiguration.contracts).Count -gt 0
}
New-Item -ItemType Directory -Force -Path $packages | Out-Null

if ($LockedMode) {
    & (Join-Path $PSScriptRoot 'Restore.ps1') -Subject $solutions[0].FullName -LockedMode
}
else {
    & (Join-Path $PSScriptRoot 'Restore.ps1') -Subject $solutions[0].FullName
}
if (-not $?) { throw 'Managed repository-isolated restore failed.' }
python (Join-Path $PSScriptRoot 'release_bundle.py') prepare-pack --repository $root --packages $packages
if ($LASTEXITCODE -ne 0) { throw 'Fresh build/pack input capture failed.' }
if ($VerifyArchitecture) {
    python (Join-Path $PSScriptRoot 'repository_architecture.py') --repository $root `
        --manifest eng/architecture.json --configuration Release --build-subject $solutions[0].FullName `
        --version $version --output artifacts/tests/architecture.xml
    if ($LASTEXITCODE -ne 0) { throw 'Fresh build/architecture checks failed.' }
}
else {
    dotnet build $solutions[0].FullName -c Release --no-restore -p:Version=$version
    if ($LASTEXITCODE -ne 0) { throw 'dotnet build failed.' }
}

if (-not $SkipTests) {
    $testProjectCount = Get-TestProjectCount -SolutionPath $solutions[0].FullName
    if ($testProjectCount -gt 0) {
        dotnet test --solution $solutions[0].FullName -c Release --no-build -p:Version=$version
        if ($LASTEXITCODE -ne 0) { throw 'dotnet test failed.' }
    }
    else {
        Write-Host 'No .NET test projects are included in the solution; skipping dotnet test.'
    }
}

dotnet pack $solutions[0].FullName -c Release --no-build -p:Version=$version -p:PackageOutputPath=$packages
if ($LASTEXITCODE -ne 0) { throw 'dotnet pack failed.' }
python (Join-Path $PSScriptRoot 'release_bundle.py') seal-pack --repository $root --packages $packages
if ($LASTEXITCODE -ne 0) { throw 'Build/pack input or output integrity check failed.' }

if (-not $SkipReleaseBundle -or $openApiEnabled) {
    $stageArguments = @('stage', '--repository', $root, '--packages', $packages,
        '--output', (Join-Path $artifacts 'release-bundle'), '--inventory', (Join-Path $packages 'program-kit-pack.json'))
    foreach ($packageId in $RootPackage) { $stageArguments += @('--root-package', $packageId) }
    python (Join-Path $PSScriptRoot 'release_bundle.py') @stageArguments
    if ($LASTEXITCODE -ne 0) { throw 'Release-bundle staging failed.' }
}

if ($openApiEnabled) {
    $openApiArguments = @('--repository', $root, '--registry', 'eng/openapi-contracts.json')
    if ($InitializeOpenApiBaseline) { $openApiArguments += '--initialize-baselines' }
    if ($UpdateOpenApiArtifact) { $openApiArguments += '--update-artifacts' }
    python (Join-Path $PSScriptRoot 'openapi_pipeline.py') @openApiArguments
    if ($LASTEXITCODE -ne 0) { throw 'Producer-first OpenAPI contract pipeline failed.' }
}
