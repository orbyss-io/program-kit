using System;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.Providers.DotNet.Templates;

public static class DotNetTemplates
{
    public static string ComponentProject(JsonObject component)
    {
        string packageId = Required(component, "packageId");
        string version = Required(component, "version");
        return $$"""
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <LangVersion>14.0</LangVersion>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally>
            <RestoreLockedMode>false</RestoreLockedMode>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <Deterministic>true</Deterministic>
            <PackageId>{{packageId}}</PackageId>
            <Version>{{version}}</Version>
            <EnforceCodeStyleInBuild>false</EnforceCodeStyleInBuild>
            <NoWarn>$(NoWarn);IDE0005</NoWarn>
            <Authors>Consumer</Authors>
            <Description>Consumer-owned Program Kit component.</Description>
            <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
          </PropertyGroup>
          <ItemGroup>
            <PackageReference Include="CShells.AspNetCore.Abstractions" Version="[0.0.28]" />
          </ItemGroup>
        </Project>
        """;
    }

    public static string ApplicationProject(JsonObject application, JsonObject component)
    {
        string packageId = Required(component, "packageId");
        string version = Required(component, "version");
        return $$"""
        <Project Sdk="Microsoft.NET.Sdk.Web">
          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <LangVersion>14.0</LangVersion>
            <ManagePackageVersionsCentrally>false</ManagePackageVersionsCentrally>
            <RestoreLockedMode>false</RestoreLockedMode>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <Deterministic>true</Deterministic>
            <EnforceCodeStyleInBuild>false</EnforceCodeStyleInBuild>
            <NoWarn>$(NoWarn);IDE0005</NoWarn>
            <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
          </PropertyGroup>
          <ItemGroup>
            <PackageReference Include="CShells.AspNetCore" Version="[0.0.28]" />
            <PackageReference Include="{{packageId}}" Version="[{{version}}]" />
          </ItemGroup>
        </Project>
        """;
    }

    public static string ProgramSource(JsonObject component)
    {
        string featureNamespace = Required(component, "namespace");
        string featureClass = Required(component, "featureClass");
        return $$"""
        using CShells.AspNetCore.Extensions;
        using CShells.DependencyInjection;
        using Microsoft.AspNetCore.Builder;
        using Microsoft.Extensions.DependencyInjection;
        using {{featureNamespace}};

        WebApplicationBuilder builder = WebApplication.CreateBuilder(args);
        builder.AddShells(shells =>
        {
            shells.WithConfigurationProvider(builder.Configuration);
            shells.WithAssemblies(typeof({{featureClass}}).Assembly);
        });

        WebApplication app = builder.Build();
        app.MapShells();
        app.Run();

        public partial class Program;
        """;
    }

    public static string AppSettings(JsonObject component)
    {
        string featureName = Required(component, "featureName");
        return $$"""
        {
          "CShells": {
            "Shells": {
              "Default": {
                "Features": {
                  "{{featureName}}": {}
                },
                "Configuration": {
                  "WebRouting": {
                    "Path": ""
                  }
                }
              }
            }
          }
        }
        """;
    }

    public static string NuGetConfig(string packageId, string componentFeed, string dependencyFeed) => $$"""
        <?xml version="1.0" encoding="utf-8"?>
        <configuration>
          <packageSources>
            <clear />
            <add key="component" value="{{componentFeed}}" />
            <add key="dependencies" value="{{dependencyFeed}}" />
          </packageSources>
          <packageSourceMapping>
            <clear />
            <packageSource key="component">
              <package pattern="{{packageId}}" />
            </packageSource>
            <packageSource key="dependencies">
              <package pattern="*" />
            </packageSource>
          </packageSourceMapping>
        </configuration>
        """;

    private static string Required(JsonObject value, string name) =>
        value[name]?.GetValue<string>() is { Length: > 0 } result
            ? result
            : throw new InvalidOperationException($"definition field {name} is required.");
}
