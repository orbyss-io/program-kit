using System.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Generation.Aspire;
using Orbyss.ProgramKit.SecretResolution.Contracts;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Aspire;

[TestClass]
[DoNotParallelize]
public sealed class AspireAppHostConformanceTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task GeneratedAppHostBuildsWithoutStartingResourcesOrReferencingProgramKit()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-aspire-conformance-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            AspireAppHostGenerator generator = new();
            var first = generator.Generate(Definition());
            var second = generator.Generate(Definition());
            Assert.AreEqual(first.OutputTreeSha256, second.OutputTreeSha256);

            var appHost = Path.Combine(root, "AppHost");
            var api = Path.Combine(root, "Fixture.Api");
            Directory.CreateDirectory(appHost);
            Directory.CreateDirectory(api);
            foreach (var output in first.Outputs)
            {
                var path = Path.Combine(
                    appHost,
                    output.RelativePath.Replace('/', Path.DirectorySeparatorChar));
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                await File.WriteAllBytesAsync(
                    path,
                    output.Content.ToArray(),
                    TestContext.CancellationToken);
            }

            await File.WriteAllTextAsync(
                Path.Combine(api, "Fixture.Api.csproj"),
                """
                <Project Sdk="Microsoft.NET.Sdk">
                  <PropertyGroup>
                    <OutputType>Exe</OutputType>
                    <TargetFramework>net10.0</TargetFramework>
                    <Nullable>enable</Nullable>
                    <ImplicitUsings>enable</ImplicitUsings>
                  </PropertyGroup>
                </Project>
                """,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                Path.Combine(api, "Program.cs"),
                "global::System.Console.WriteLine(\"fixture\");\n",
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                Path.Combine(appHost, "NuGet.Config"),
                """
                <?xml version="1.0" encoding="utf-8"?>
                <configuration>
                  <packageSources>
                    <clear />
                    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" protocolVersion="3" />
                  </packageSources>
                  <packageSourceMapping>
                    <clear />
                    <packageSource key="nuget.org">
                      <package pattern="*" />
                    </packageSource>
                  </packageSourceMapping>
                </configuration>
                """,
                TestContext.CancellationToken);

            var restore = await RunAsync(
                appHost,
                "restore",
                "AppHost.csproj",
                "--configfile",
                "NuGet.Config",
                "--force-evaluate",
                "--verbosity",
                "minimal");
            Assert.AreEqual(0, restore.ExitCode, restore.Output);
            var build = await RunAsync(
                appHost,
                "build",
                "AppHost.csproj",
                "--no-restore",
                "--configuration",
                "Release",
                "--verbosity",
                "minimal");
            Assert.AreEqual(0, build.ExitCode, build.Output);

            var assets = await File.ReadAllTextAsync(
                Path.Combine(appHost, "obj", "project.assets.json"),
                TestContext.CancellationToken);
            Assert.DoesNotContain("Orbyss.ProgramKit", assets);
            Assert.Contains("Aspire.Hosting.AppHost/13.4.6", assets);
            Assert.IsFalse(Directory.Exists(Path.Combine(appHost, ".aspire")));
            Assert.IsFalse(Directory.Exists(Path.Combine(appHost, "logs")));
            Assert.Contains(
                "\"state\": \"deferred-to-separate-human-started-restore\"",
                await File.ReadAllTextAsync(
                    Path.Combine(appHost, "aspire-apphost.lock.json"),
                    TestContext.CancellationToken));
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, true);
            }
        }
    }

    private static AspireAppHostDefinition Definition() =>
        new(
            new ProgramKitIdentifier("pkid:apphost:fixture:local-composition"),
            new SemanticVersion("1.0.0"),
            [
                new AspireIntegrationSelection(
                    AspireIntegrationCatalog.AppHost.Identity,
                    AspireIntegrationCatalog.AppHost.Version),
            ],
            [
                new AspireParameterDefinition(
                    "database-password",
                    "Parameters:database-password",
                    SecretReference()),
                new AspireParameterDefinition("log-level", "Parameters:log-level", null),
            ],
            [
                new AspireResourceDefinition(
                    "api",
                    AspireResourceKind.Project,
                    "../Fixture.Api/Fixture.Api.csproj",
                    "FixtureApi",
                    null,
                    null,
                    [],
                    null),
                new AspireResourceDefinition(
                    "database",
                    AspireResourceKind.Container,
                    null,
                    null,
                    null,
                    null,
                    ["-c", "max_connections=100"],
                    string.Concat("postgres@sha256:", new string('a', 64))),
                new AspireResourceDefinition(
                    "migration",
                    AspireResourceKind.Executable,
                    null,
                    null,
                    "../tools/migrate",
                    "../tools",
                    ["--apply"],
                    null),
            ],
            [
                new AspireEndpointDefinition(
                    "api",
                    "http",
                    "http",
                    8080,
                    null,
                    true,
                    true),
                new AspireEndpointDefinition(
                    "database",
                    "tcp",
                    "tcp",
                    5432,
                    null,
                    false,
                    true),
            ],
            [
                new AspireEnvironmentBinding("api", "LOG_LEVEL", "log-level"),
                new AspireEnvironmentBinding(
                    "database",
                    "POSTGRES_PASSWORD",
                    "database-password"),
            ],
            [new AspireResourceReference("api", "database", "tcp")],
            [new AspireWaitDependency("migration", "database")],
            [new AspireVolumeDefinition("database", "database-data", "/var/lib/postgresql/data", false)]);

    private static SecretReferenceDescriptor SecretReference()
    {
        var resolver = Reference("pkid:capability:fixture:secret-resolver");
        return new SecretReferenceDescriptor(
            new ProgramKitIdentifier("pkid:secret-reference:fixture:database-password"),
            SecretReferenceClassification.RestrictedMetadata,
            SecretResultKind.ConfigurationText,
            resolver,
            Reference("pkid:locator:fixture:database-password"),
            SecretReferenceClassification.SensitiveMetadata);
    }

    private static ArtifactReference Reference(string identity) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(string.Concat("sha256:", new string('b', 64))));

    private static async Task<(int ExitCode, string Output)> RunAsync(
        string workingDirectory,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo) ??
            throw new InvalidOperationException("The bounded dotnet process did not start.");
        var standardOutput = process.StandardOutput.ReadToEndAsync();
        var standardError = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        return (
            process.ExitCode,
            string.Concat(
                await standardOutput,
                Environment.NewLine,
                await standardError));
    }
}
