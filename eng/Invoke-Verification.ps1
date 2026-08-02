[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('Edit', 'Story', 'PrePr', 'Ci', 'Human', 'Fast', 'Contract')]
    [string]$Mode = 'Edit',

    [Parameter()]
    [string]$TestFilter,

    [Parameter()]
    [switch]$IncludeAcceptance
)

$ErrorActionPreference = 'Stop'
$effectiveMode = switch ($Mode) {
    'Fast' { 'Edit' }
    'Contract' { 'Story' }
    default { $Mode }
}
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$toolHome = Join-Path $repositoryRoot 'artifacts/work/verification-tool-home'
[IO.Directory]::CreateDirectory($toolHome) | Out-Null
$priorEnvironment = @{
    DOTNET_CLI_HOME = $env:DOTNET_CLI_HOME
    DOTNET_CLI_TELEMETRY_OPTOUT = $env:DOTNET_CLI_TELEMETRY_OPTOUT
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE = $env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE
    DOTNET_NOLOGO = $env:DOTNET_NOLOGO
    NUGET_XMLDOC_MODE = $env:NUGET_XMLDOC_MODE
    APPDATA = $env:APPDATA
    XDG_CONFIG_HOME = $env:XDG_CONFIG_HOME
}

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
    $env:DOTNET_CLI_HOME = $toolHome
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    $env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
    $env:DOTNET_NOLOGO = '1'
    $env:NUGET_XMLDOC_MODE = 'skip'
    if ($IsWindows) {
        $env:APPDATA = $toolHome
    }
    else {
        $env:XDG_CONFIG_HOME = $toolHome
    }

    Invoke-Checked { & (Join-Path $PSScriptRoot 'Assert-SpecKitIntegrity.ps1') } 'Spec Kit project integrity failed.'
    Invoke-Checked { & (Join-Path $PSScriptRoot 'Assert-CanonicalText.ps1') } 'Canonical text verification failed.'

    if ($effectiveMode -eq 'Human') {
        Write-Host 'Human verification is a post-CI review checkpoint. This mode launches no provider, repeats no automated gate, and records no acceptance by itself.'
        return
    }

    if ($effectiveMode -eq 'Edit') {
        Invoke-Checked {
            if ($TestFilter) {
                dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration Debug --no-restore --filter $TestFilter
            }
            else {
                dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration Debug --no-restore
            }
        } 'Fast unit verification failed. If dependency inputs changed, run PrePr once to perform a locked restore.'

        Write-Host 'Edit verification passed. Story, pre-PR, CI, and human proof remain at their declared checkpoints.'
        return
    }

    if ($effectiveMode -eq 'Story') {
        Invoke-Checked {
            dotnet build src/ProgramKit.Cli/ProgramKit.Cli.csproj --configuration ContractLoop --no-restore
        } 'CLI build failed. If dependency inputs changed, run PrePr once to perform a locked restore.'
        Invoke-Checked {
            dotnet build tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration ContractLoop --no-restore
        } 'Unit build failed. If dependency inputs changed, run PrePr once to perform a locked restore.'
        Invoke-Checked {
            dotnet build tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --configuration ContractLoop --no-restore
        } 'Contract build failed. If dependency inputs changed, run PrePr once to perform a locked restore.'
        if ($IncludeAcceptance) {
            Invoke-Checked {
                dotnet build tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --configuration ContractLoop --no-restore
            } 'Acceptance build failed. If dependency inputs changed, run PrePr once to perform a locked restore.'
        }
        Invoke-Checked {
            if ($TestFilter) {
                dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration ContractLoop --no-build --no-restore --filter $TestFilter
            }
            else {
                dotnet test tests/ProgramKit.UnitTests/ProgramKit.UnitTests.csproj --configuration ContractLoop --no-build --no-restore
            }
        } 'Unit verification failed.'
        Invoke-Checked {
            if ($TestFilter) {
                dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --configuration ContractLoop --no-build --no-restore --filter $TestFilter
            }
            else {
                dotnet test tests/ProgramKit.ContractTests/ProgramKit.ContractTests.csproj --configuration ContractLoop --no-build --no-restore
            }
        } 'Contract verification failed.'
        if ($IncludeAcceptance) {
            Invoke-Checked {
                if ($TestFilter) {
                    dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --configuration ContractLoop --no-build --no-restore --filter $TestFilter
                }
                else {
                    dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --configuration ContractLoop --no-build --no-restore
                }
            } 'Acceptance verification failed.'
        }

        Write-Host 'Story verification passed. Unselected acceptance, evidence regeneration, and platform proof remain CI-owned.'
        return
    }

    if ($effectiveMode -eq 'Ci') {
        if ($env:GITHUB_ACTIONS -ne 'true') {
            throw 'CI verification is protected-runner-only; use PrePr locally.'
        }
        Invoke-Checked { & (Join-Path $PSScriptRoot 'Bootstrap-DependencyMirror.ps1') } 'Dependency mirror bootstrap failed.'
        Invoke-Checked { dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.Config -p:NuGetAudit=false } 'Locked restore failed.'
        Invoke-Checked { dotnet build ProgramKit.slnx --configuration Release --no-restore } 'Release build failed.'
        Invoke-Checked { & (Join-Path $PSScriptRoot 'Generate-DistributionEvidence.ps1') } 'Distribution evidence generation failed.'
        Invoke-Checked { & git diff --exit-code -- artifacts/evidence } 'Checked-in distribution evidence is stale.'
        Invoke-Checked { dotnet test ProgramKit.slnx --configuration Release --no-build --no-restore --filter 'TestCategory!=PlatformLifecycle' } 'Authoritative platform-neutral Ubuntu test proof failed.'
        Invoke-Checked { dotnet format ProgramKit.slnx --no-restore --verify-no-changes } 'Repository formatting verification failed.'
        Invoke-Checked { & git diff --check } 'Git whitespace verification failed.'
        Write-Host 'CI core verification passed once. The workflow-owned platform job runs only package/process/path/lifecycle/end-to-end proof.'
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
    $mirrorInputsChanged = @(
        & git diff HEAD --name-only -- eng/dependency-mirror.manifest.json eng/Bootstrap-DependencyMirror.ps1 NuGet.Config
        & git ls-files --others --exclude-standard -- eng/dependency-mirror.manifest.json eng/Bootstrap-DependencyMirror.ps1 NuGet.Config
    ) | Where-Object { $_ }
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not determine whether dependency-mirror inputs changed.'
    }
    $mirrorMissing = -not (Test-Path -LiteralPath 'artifacts/dependency-mirror/mirror.lock.json' -PathType Leaf)
    if ($mirrorInputsChanged.Count -gt 0 -or $mirrorMissing) {
        Invoke-Checked { & (Join-Path $PSScriptRoot 'Bootstrap-DependencyMirror.ps1') } 'Dependency mirror bootstrap failed.'
    }
    else {
        Write-Host 'Dependency-mirror inputs are unchanged and the local mirror exists; reusing it.'
    }
    if ($dependencyChanges.Count -gt 0 -or $missingAssets.Count -gt 0) {
        Invoke-Checked {
            dotnet restore ProgramKit.slnx --locked-mode --configfile NuGet.Config -p:NuGetAudit=false
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
    Invoke-Checked {
        dotnet test tests/ProgramKit.AcceptanceTests/ProgramKit.AcceptanceTests.csproj --configuration PrePr --no-build --no-restore --filter 'FullyQualifiedName~SpecKitAdapterBootstrapAcceptanceTests'
    } 'Pre-PR staged-extension smoke failed.'

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
    foreach ($entry in $priorEnvironment.GetEnumerator()) {
        if ($null -eq $entry.Value) {
            Remove-Item -LiteralPath "Env:$($entry.Key)" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item -LiteralPath "Env:$($entry.Key)" -Value $entry.Value
        }
    }
}
