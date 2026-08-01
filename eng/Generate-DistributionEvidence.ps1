[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$toolHome = Join-Path $repositoryRoot 'artifacts/work/evidence-tool-home'
[IO.Directory]::CreateDirectory($toolHome) | Out-Null
$priorEnvironment = @{
    DOTNET_CLI_HOME = $env:DOTNET_CLI_HOME
    DOTNET_CLI_TELEMETRY_OPTOUT = $env:DOTNET_CLI_TELEMETRY_OPTOUT
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE = $env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE
    DOTNET_NOLOGO = $env:DOTNET_NOLOGO
    DOTNET_CLI_UI_LANGUAGE = $env:DOTNET_CLI_UI_LANGUAGE
    NUGET_XMLDOC_MODE = $env:NUGET_XMLDOC_MODE
    APPDATA = $env:APPDATA
    XDG_CONFIG_HOME = $env:XDG_CONFIG_HOME
}
Push-Location $repositoryRoot
try {
    $env:DOTNET_CLI_HOME = $toolHome
    $env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    $env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
    $env:DOTNET_NOLOGO = '1'
    $env:DOTNET_CLI_UI_LANGUAGE = 'en-US'
    $env:NUGET_XMLDOC_MODE = 'skip'
    if ($IsWindows) {
        $env:APPDATA = $toolHome
    }
    else {
        $env:XDG_CONFIG_HOME = $toolHome
    }

    & dotnet run --file (Join-Path $PSScriptRoot 'GenerateDistributionEvidence.cs')
    if ($LASTEXITCODE -ne 0) {
        throw "Distribution evidence generation failed with exit code $LASTEXITCODE."
    }
    git diff --check -- artifacts/evidence
    if ($LASTEXITCODE -ne 0) {
        throw 'Generated distribution evidence contains invalid whitespace.'
    }
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
