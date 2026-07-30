using System.Diagnostics;
using System.Text;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Publication;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Sealing;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Verification;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Operations;

[TestClass]
public sealed class GeneratedOutputIntegrityBuildTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task BuildVerifiesBeforeCompilationAndTamperFailsClosed()
    {
        var temporaryRoot = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-integrity-build-tests-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(temporaryRoot);
        try
        {
            var repository = FindProgramKitRoot();
            var targets = Path.Combine(
                repository,
                "src",
                "Orbyss.ProgramKit.GeneratedOutputIntegrity.Build",
                "build",
                "Orbyss.ProgramKit.GeneratedOutputIntegrity.Build.targets");
            var taskAssembly = Path.Combine(
                repository,
                "src",
                "Orbyss.ProgramKit.GeneratedOutputIntegrity.Build",
                "bin",
                "Release",
                "net10.0",
                "Orbyss.ProgramKit.GeneratedOutputIntegrity.Build.dll");
            Assert.IsTrue(File.Exists(taskAssembly));
            var host = Path.Combine(temporaryRoot, "host");
            GeneratedOutputPublisher publisher = new(
                new GeneratedOutputSealer(),
                new GeneratedOutputIntegrityVerifier());
            _ = await publisher.PublishCreateAsync(
                host,
                [
                    Payload(
                        "GeneratedHost.csproj",
                        string.Concat(
                            """
                            <Project Sdk="Microsoft.NET.Sdk">
                              <PropertyGroup>
                                <TargetFramework>net10.0</TargetFramework>
                                <OutputType>Exe</OutputType>
                                <ProgramKitGeneratedOutputIntegrityTaskAssembly>
                            """,
                            Xml(taskAssembly),
                            """
                            </ProgramKitGeneratedOutputIntegrityTaskAssembly>
                              </PropertyGroup>
                              <Import Project="
                            """,
                            Xml(targets),
                            """
                            " />
                            </Project>

                            """)),
                    Payload(
                        "Directory.Build.props",
                        """
                        <Project>
                          <PropertyGroup>
                            <TargetFramework>net10.0</TargetFramework>
                            <BaseOutputPath>$(MSBuildProjectDirectory)\..\.build\bin\</BaseOutputPath>
                            <BaseIntermediateOutputPath>$(MSBuildProjectDirectory)\..\.build\obj\</BaseIntermediateOutputPath>
                            <OutputPath>$(BaseOutputPath)$(Configuration)\$(TargetFramework)\</OutputPath>
                            <IntermediateOutputPath>$(BaseIntermediateOutputPath)$(Configuration)\$(TargetFramework)\</IntermediateOutputPath>
                            <MSBuildProjectExtensionsPath>$(BaseIntermediateOutputPath)</MSBuildProjectExtensionsPath>
                          </PropertyGroup>
                        </Project>

                        """),
                    Payload(
                        "Directory.Build.targets",
                        """
                        <Project>
                          <Target Name="ProgramKitConfigureGeneratedProjectVerification">
                            <PropertyGroup>
                              <ProgramKitCSharpGateGeneratedProjectBinding>1.0.0</ProgramKitCSharpGateGeneratedProjectBinding>
                            </PropertyGroup>
                          </Target>

                          <Target Name="ProgramKitVerifyGeneratedProject"
                                  DependsOnTargets="ProgramKitConfigureGeneratedProjectVerification;Build" />
                        </Project>

                        """),
                    Payload(
                        "ProgramKitGenerated/Program.cs",
                        """
                        namespace GeneratedHost;

                        internal static class Program
                        {
                            private static void Main()
                            {
                            }
                        }

                        """),
                    Payload(
                        "ProgramKitGenerated/Hosting/ProgramKitGeneratedIntegrityRequirement.cs",
                        """
                        namespace GeneratedHost.Hosting;

                        internal sealed class ProgramKitGeneratedIntegrityRequirement :
                            ProgramKitGeneratedIntegrityAttestation;

                        """),
                ],
                TestContext.CancellationToken);

            var restore = await RunDotNetAsync(
                host,
                ["restore", "GeneratedHost.csproj", "--nologo"],
                TestContext.CancellationToken);
            Assert.AreEqual(0, restore.ExitCode, restore.Output);
            var valid = await RunDotNetAsync(
                host,
                [
                    "build",
                    "GeneratedHost.csproj",
                    "--no-restore",
                    "--no-incremental",
                    "--nologo",
                    "-t:ProgramKitVerifyGeneratedProject",
                ],
                TestContext.CancellationToken);
            Assert.AreEqual(0, valid.ExitCode, valid.Output);

            await File.AppendAllTextAsync(
                Path.Combine(host, "ProgramKitGenerated", "Program.cs"),
                "// tampered\n",
                new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
                TestContext.CancellationToken);
            var tampered = await RunDotNetAsync(
                host,
                [
                    "build",
                    "GeneratedHost.csproj",
                    "--no-restore",
                    "--nologo",
                    "-t:ProgramKitVerifyGeneratedProject",
                ],
                TestContext.CancellationToken);

            Assert.AreNotEqual(0, tampered.ExitCode);
            Assert.IsTrue(
                tampered.Output.Contains(
                    "PKINT100",
                    StringComparison.Ordinal));
            Assert.IsTrue(
                tampered.Output.Contains(
                    "Tampered-with Program Kit generated output",
                    StringComparison.Ordinal));

            var projectPath = Path.Combine(host, "GeneratedHost.csproj");
            var project = await File.ReadAllTextAsync(
                projectPath,
                TestContext.CancellationToken);
            var importStart = project.IndexOf(
                "  <Import Project=",
                StringComparison.Ordinal);
            Assert.IsGreaterThanOrEqualTo(0, importStart);
            var importEnd = project.IndexOf(
                "/>",
                importStart,
                StringComparison.Ordinal);
            Assert.IsGreaterThan(importStart, importEnd);
            project = project.Remove(
                importStart,
                (importEnd + 2) - importStart);
            await File.WriteAllTextAsync(
                projectPath,
                project,
                new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
                TestContext.CancellationToken);
            await ResealAsync(host, TestContext.CancellationToken);

            var missingTarget = await RunDotNetAsync(
                host,
                [
                    "build",
                    "GeneratedHost.csproj",
                    "--no-restore",
                    "--no-incremental",
                    "--nologo",
                ],
                TestContext.CancellationToken);
            Assert.AreNotEqual(
                0,
                missingTarget.ExitCode,
                missingTarget.Output);
            Assert.IsTrue(
                missingTarget.Output.Contains(
                    "ProgramKitGeneratedIntegrityAttestation",
                    StringComparison.Ordinal));
        }
        finally
        {
            if (Directory.Exists(temporaryRoot))
            {
                Directory.Delete(temporaryRoot, recursive: true);
            }
        }
    }

    private static GeneratedOutputPayload Payload(
        string relativePath,
        string content)
    {
        UTF8Encoding encoding = new(
            encoderShouldEmitUTF8Identifier: false);
        return new GeneratedOutputPayload(
            relativePath,
            encoding.GetBytes(content));
    }

    private static async Task<(int ExitCode, string Output)> RunDotNetAsync(
        string workingDirectory,
        IEnumerable<string> arguments,
        CancellationToken cancellationToken)
    {
        ProcessStartInfo start = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (var argument in arguments)
        {
            start.ArgumentList.Add(argument);
        }

        using var process = Process.Start(start) ??
            throw new InvalidOperationException("dotnet did not start.");
        var standardOutput = process.StandardOutput.ReadToEndAsync(
            cancellationToken);
        var standardError = process.StandardError.ReadToEndAsync(
            cancellationToken);
        await process.WaitForExitAsync(cancellationToken);
        return (
            process.ExitCode,
            string.Concat(
                await standardOutput,
                Environment.NewLine,
                await standardError));
    }

    private static async Task ResealAsync(
        string root,
        CancellationToken cancellationToken)
    {
        var payloads = new List<GeneratedOutputPayload>();
        foreach (var path in Directory.EnumerateFiles(
                     root,
                     "*",
                     SearchOption.AllDirectories))
        {
            var relative = Path.GetRelativePath(root, path).Replace('\\', '/');
            if (string.Equals(
                    relative,
                    GeneratedOutputIntegrityConstants.ManifestRelativePath,
                    StringComparison.Ordinal))
            {
                continue;
            }

            payloads.Add(
                new GeneratedOutputPayload(
                    relative,
                    await File.ReadAllBytesAsync(
                        path,
                        cancellationToken)));
        }

        GeneratedOutputSealer sealer = new();
        var seal = sealer.Seal(payloads);
        await File.WriteAllBytesAsync(
            GeneratedOutputPathPolicy.ResolveUnderRoot(
                root,
                GeneratedOutputIntegrityConstants.ManifestRelativePath,
                allowManifest: true),
            seal.ManifestBytes.ToArray(),
            cancellationToken);
        await File.WriteAllBytesAsync(
            GeneratedOutputPathPolicy.AnchorPath(root),
            seal.AnchorBytes.ToArray(),
            cancellationToken);
    }

    private static string FindProgramKitRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current.FullName;
            }

            current = current.Parent;
        }

        throw new InvalidOperationException(
            "The Program Kit repository root could not be found.");
    }

    private static string Xml(string value) =>
        value
            .Replace("&", "&amp;", StringComparison.Ordinal)
            .Replace("\"", "&quot;", StringComparison.Ordinal)
            .Replace("<", "&lt;", StringComparison.Ordinal)
            .Replace(">", "&gt;", StringComparison.Ordinal);
}
