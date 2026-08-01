[CmdletBinding()]
param(
    [string] $OutputRoot = "artifacts/dependency-mirror"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$resolvedOutput = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $OutputRoot))
if (-not $resolvedOutput.StartsWith($repositoryRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Dependency mirror must remain beneath the repository root."
}

$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot "dependency-mirror.manifest.json") -Raw | ConvertFrom-Json
$bootstrapRoot = Join-Path ([IO.Path]::GetTempPath()) ("program-kit-mirror-" + [guid]::NewGuid().ToString("N"))
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
try {
    New-Item -ItemType Directory -Path $bootstrapRoot | Out-Null
    $toolHome = Join-Path $bootstrapRoot 'tool-home'
    [IO.Directory]::CreateDirectory($toolHome) | Out-Null
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

    $projectPath = Join-Path $bootstrapRoot "mirror.csproj"
    $packageItems = foreach ($package in $manifest.packages | Where-Object { $_.id -in @('CShells.AspNetCore', 'CShells.AspNetCore.Abstractions') }) {
        "    <PackageReference Include=`"$($package.id)`" Version=`"[$($package.version)]`" />"
    }
    @(
        '<Project Sdk="Microsoft.NET.Sdk">',
        '  <PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup>',
        '  <ItemGroup>',
        $packageItems,
        '  </ItemGroup>',
        '</Project>'
    ) | Set-Content -LiteralPath $projectPath -Encoding utf8
    $packagesPath = Join-Path $bootstrapRoot "packages"
    dotnet restore $projectPath --packages $packagesPath --configfile (Join-Path $repositoryRoot "NuGet.Config") --no-cache
    if ($LASTEXITCODE -ne 0) { throw "Dependency closure restore failed." }

    $assets = Get-Content -LiteralPath (Join-Path $bootstrapRoot "obj/project.assets.json") -Raw | ConvertFrom-Json -Depth 100
    $packages = $assets.libraries.PSObject.Properties |
        Where-Object { $_.Value.type -eq 'package' } |
        ForEach-Object {
            $separator = $_.Name.LastIndexOf('/')
            [pscustomobject]@{ id = $_.Name.Substring(0, $separator); version = $_.Name.Substring($separator + 1) }
        } |
        Sort-Object id, version -Unique

    New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
    $locked = foreach ($package in $packages) {
        $packageId = $package.id.ToLowerInvariant()
        $packageFile = Join-Path $resolvedOutput "$packageId.$($package.version).nupkg"
        $packageUri = "https://api.nuget.org/v3-flatcontainer/$packageId/$($package.version)/$packageId.$($package.version).nupkg"
        Invoke-WebRequest -Uri $packageUri -OutFile $packageFile
        [pscustomobject]@{ id = $package.id; version = $package.version; sha256 = "sha256:$((Get-FileHash -LiteralPath $packageFile -Algorithm SHA256).Hash.ToLowerInvariant())" }
    }
    [ordered]@{ schema = 'program-kit.dependency-mirror-lock/v1'; packages = @($locked) } |
        ConvertTo-Json -Depth 10 |
        Set-Content -LiteralPath (Join-Path $resolvedOutput 'mirror.lock.json') -Encoding utf8
} finally {
    foreach ($entry in $priorEnvironment.GetEnumerator()) {
        if ($null -eq $entry.Value) {
            Remove-Item -LiteralPath "Env:$($entry.Key)" -ErrorAction SilentlyContinue
        }
        else {
            Set-Item -LiteralPath "Env:$($entry.Key)" -Value $entry.Value
        }
    }

    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $resolvedBootstrap = [IO.Path]::GetFullPath($bootstrapRoot)
    if ($resolvedBootstrap.StartsWith($tempRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $resolvedBootstrap)) {
        Remove-Item -LiteralPath $resolvedBootstrap -Recurse -Force
    }
}
