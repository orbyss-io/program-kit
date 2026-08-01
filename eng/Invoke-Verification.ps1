[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('Fast', 'Contract', 'PrePr')]
    [string]$Mode = 'Fast'
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory)][scriptblock]$Command,
        [Parameter(Mandatory)][string]$FailureMessage
    )

    $global:LASTEXITCODE = 0
    & $Command
    $commandSucceeded = $?
    if (-not $commandSucceeded -or $LASTEXITCODE -ne 0) {
        throw $FailureMessage
    }
}

Push-Location $repositoryRoot
try {
    Invoke-Checked { & (Join-Path $PSScriptRoot 'Assert-SpecKitIntegrity.ps1') } 'Spec Kit project integrity failed.'
    Invoke-Checked { & (Join-Path $PSScriptRoot 'Assert-CanonicalText.ps1') } 'Canonical text verification failed.'

    if ($Mode -eq 'Fast') {
        Invoke-Checked {
            dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration Debug --no-restore
        } 'Fast unit verification failed. If dependency inputs changed, run PrePr once to perform a locked restore.'

        Write-Host 'Fast verification passed. Acceptance, conformance, evidence regeneration, and platform proof remain CI-owned.'
        return
    }

    if ($Mode -eq 'Contract') {
        Invoke-Checked {
            dotnet build src/ProgramKit.Cli/ProgramKit.Cli.csproj --configuration ContractLoop --no-restore
        } 'CLI build failed. If dependency inputs changed, run PrePr once to perform a locked restore.'
        Invoke-Checked {
            dotnet build tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration ContractLoop --no-restore
        } 'Unit build failed. If dependency inputs changed, run PrePr once to perform a locked restore.'
        Invoke-Checked {
            dotnet build tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --configuration ContractLoop --no-restore
        } 'Contract build failed. If dependency inputs changed, run PrePr once to perform a locked restore.'
        Invoke-Checked {
            dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration ContractLoop --no-build --no-restore
        } 'Unit verification failed.'
        Invoke-Checked {
            dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --configuration ContractLoop --no-build --no-restore
        } 'Contract verification failed.'

        Write-Host 'Contract verification passed. Full acceptance, evidence regeneration, and platform proof remain CI-owned.'
        return
    }

    $dependencyChanges = @(
        & git diff HEAD --name-only -- global.json Directory.Packages.props NuGet.Config ':(glob)**/*.csproj' ':(glob)**/packages.lock.json'
        & git ls-files --others --exclude-standard -- '*.csproj' 'packages.lock.json'
    ) | Where-Object { $_ }
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not determine whether dependency inputs changed.'
    }
    $missingAssets = Get-ChildItem -Recurse -Filter '*.csproj' | Where-Object {
        -not (Test-Path -LiteralPath (Join-Path $_.DirectoryName 'obj/project.assets.json'))
    }
    if ($dependencyChanges.Count -gt 0 -or $missingAssets.Count -gt 0) {
        Invoke-Checked { & (Join-Path $PSScriptRoot 'Bootstrap-DependencyMirror.ps1') } 'Dependency mirror bootstrap failed.'
        Invoke-Checked {
            dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.Config
        } 'Locked restore failed.'
    }
    else {
        Write-Host 'Dependency inputs and restore assets are unchanged; reusing the existing locked restore.'
    }
    $prePrProjects = @(
        'src/ProgramKit.Cli/ProgramKit.Cli.csproj',
        'tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj',
        'tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj',
        'tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj'
    )
    foreach ($project in $prePrProjects) {
        Invoke-Checked {
            dotnet build $project --configuration PrePr --no-restore -p:Optimize=true
        } "Pre-PR isolated build failed for $project."
    }
    Invoke-Checked {
        dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration PrePr --no-build --no-restore
    } 'Pre-PR unit verification failed.'
    Invoke-Checked {
        dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --configuration PrePr --no-build --no-restore
    } 'Pre-PR contract verification failed.'

    $changedCode = @(
        & git diff HEAD --name-only --diff-filter=ACMR -- '*.cs'
        & git ls-files --others --exclude-standard -- '*.cs'
    ) | Where-Object { $_ } | Sort-Object -Unique
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not determine changed C# files for formatting verification.'
    }

    if ($changedCode.Count -gt 0) {
        Invoke-Checked {
            dotnet format ProgramKit.slnx --no-restore --verify-no-changes --include $changedCode
        } 'Changed-file formatting verification failed.'
    }
    else {
        Write-Host 'No changed C# files require local formatting verification.'
    }

    Invoke-Checked { & git diff --check } 'Git whitespace verification failed.'
    Write-Host 'Pre-PR verification passed. CI owns full acceptance, conformance, deterministic evidence, and Windows/Linux proof.'
}
finally {
    Pop-Location
}
