using System.Diagnostics;
using System.Reflection;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Testing.Operations.Execution;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

[TestClass]
[DoNotParallelize]
public sealed class CSharpGateOperationTests
{
    private static readonly string[] VerificationRequestPropertyNames =
    [
        "Boundary",
        "Command",
        "DotNetSdkVersion",
        "EvidenceOutputPath",
        "ExceptionUseReceiptPaths",
        "MaximumCapturedOutputBytes",
        "PackagePaths",
        "ParticipationReceiptPaths",
        "PerformanceBudgetMilliseconds",
        "ProjectPath",
        "VerificationProfile",
        "WorkingDirectory",
    ];

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task ValidateAndRenderUseDataOnlyAndProduceStableProjection()
    {
        var fixture = Path.Combine(
            FindProgramKitRoot(),
            "extensions",
            "reusable-csharp-build-gates",
            "fixtures",
            "consumer-owned-build-gate-definition.json");
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-csharp-gate-operations-");
        var first = Path.Combine(temporary.FullName, "first.md");
        var second = Path.Combine(temporary.FullName, "second.md");

        TestCommandConsole validationConsole = new();
        var validation = CommandLineComposition.CreateDefault(validationConsole);
        var validationExit = await validation.RunAsync(
        [
            "csharp-gate",
            "validate-definition",
            fixture,
        ], TestContext.CancellationToken);
        Assert.AreEqual(
            CommandExitCode.Success,
            validationExit,
            Encoding.UTF8.GetString(validationConsole.StandardError));
        Assert.IsEmpty(validationConsole.StandardError);

        foreach (var output in new[] { first, second })
        {
            TestCommandConsole renderConsole = new();
            var rendering = CommandLineComposition.CreateDefault(renderConsole);
            var exit = await rendering.RunAsync(
            [
                "csharp-gate",
                "render-definition",
                fixture,
                "--output",
                output,
            ], TestContext.CancellationToken);
            Assert.AreEqual(CommandExitCode.Success, exit);
            Assert.IsEmpty(renderConsole.StandardError);
        }

        Assert.AreEqual(
            File.ReadAllText(first),
            File.ReadAllText(second));
        Assert.Contains(
            "consumer-owned",
            File.ReadAllText(first));
        Assert.DoesNotContain(
            "Orbyss.ProgramKit.CSharpGate",
            File.ReadAllText(first));
    }

    [TestMethod]
    public async Task ExactCommandProfileRejectsUnknownAndCaseChangedMembers()
    {
        var fixture = Path.Combine(
            FindProgramKitRoot(),
            "extensions",
            "reusable-csharp-build-gates",
            "fixtures",
            "consumer-owned-build-gate-definition.json");
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-csharp-gate-profile-");
        var original = File.ReadAllText(fixture);
        var cases = new[]
        {
            string.Concat("{\"unknownMember\":true,", original.AsSpan(1)),
            original.Replace(
                "\"activationMatrix\"",
                "\"ActivationMatrix\"",
                StringComparison.Ordinal),
        };

        for (var index = 0; index < cases.Length; index++)
        {
            var input = Path.Combine(temporary.FullName, $"{index}.json");
            await File.WriteAllTextAsync(
                input,
                cases[index],
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var application = CommandLineComposition.CreateDefault(console);
            var exit = await application.RunAsync(
            [
                "csharp-gate",
                "validate-definition",
                input,
            ], TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.UsageOrInputFailure, exit);
            Assert.Contains("PKCLI002", Encoding.UTF8.GetString(
                console.StandardError));
        }
    }

    [TestMethod]
    public void VerificationRequestHasNoExecutableOrArgumentSurface()
    {
        var properties = typeof(CSharpGateVerificationRequest)
            .GetProperties(BindingFlags.Instance | BindingFlags.Public)
            .Select(property => property.Name)
            .ToArray();

        Assert.DoesNotContain("Executable", properties);
        Assert.DoesNotContain("Arguments", properties);
        Assert.AreSequenceEqual(
            VerificationRequestPropertyNames,
            properties.Order(StringComparer.Ordinal));
    }

    [TestMethod]
    public async Task PinnedHarnessProducesPathRedactedAtomicEvidence()
    {
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-csharp-gate-harness-");
        var project = await CreateBuildableProjectAsync(
            temporary.FullName,
            pause: false);
        var evidence = Path.Combine(temporary.FullName, "evidence.json");
        PinnedDotNetCSharpGateCompilerHarness sut = new();

        var result = await sut.VerifyAsync(
            Request(temporary.FullName, project, evidence),
            TestContext.CancellationToken);

        Assert.IsTrue(result.Succeeded, result.ToString());
        Assert.IsTrue(File.Exists(evidence));
        var content = File.ReadAllText(evidence);
        Assert.DoesNotContain(temporary.FullName, content);
        Assert.DoesNotContain("execut", content.ToLowerInvariant());
        Assert.Contains("\"command\":\"build\"", content);
        Assert.IsEmpty(Directory.EnumerateFiles(
            temporary.FullName,
            "*.tmp",
            SearchOption.AllDirectories).ToArray());
    }

    [TestMethod]
    public async Task PinnedHarnessEvidenceIsDeterministicAcrossCleanPaths()
    {
        using CSharpGateTemporaryDirectory first =
            new("program-kit-csharp-gate-path-a-");
        using CSharpGateTemporaryDirectory second =
            new("program-kit-csharp-gate-path-b-");
        var firstProject = await CreateBuildableProjectAsync(
            first.FullName,
            pause: false);
        var secondProject = await CreateBuildableProjectAsync(
            second.FullName,
            pause: false);
        var firstEvidence = Path.Combine(first.FullName, "evidence.json");
        var secondEvidence = Path.Combine(second.FullName, "evidence.json");
        PinnedDotNetCSharpGateCompilerHarness sut = new();

        var firstResult = await sut.VerifyAsync(
            Request(first.FullName, firstProject, firstEvidence),
            TestContext.CancellationToken);
        var secondResult = await sut.VerifyAsync(
            Request(second.FullName, secondProject, secondEvidence),
            TestContext.CancellationToken);

        Assert.AreEqual(firstResult.OutputDigest, secondResult.OutputDigest);
        Assert.AreEqual(
            File.ReadAllText(firstEvidence),
            File.ReadAllText(secondEvidence));
    }

    [TestMethod]
    public async Task CancellationKillsTheFiniteProcessTreeAndPromotesNoEvidence()
    {
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-csharp-gate-cancel-");
        var project = await CreateBuildableProjectAsync(
            temporary.FullName,
            pause: true);
        var evidence = Path.Combine(temporary.FullName, "evidence.json");
        using CancellationTokenSource cancellation = new(
            TimeSpan.FromMilliseconds(500));
        PinnedDotNetCSharpGateCompilerHarness sut = new();
        var stopwatch = Stopwatch.StartNew();

        await Assert.ThrowsAsync<OperationCanceledException>(
            async () => await sut.VerifyAsync(
                Request(temporary.FullName, project, evidence),
                cancellation.Token));
        stopwatch.Stop();

        Assert.IsLessThan(10_000, stopwatch.ElapsedMilliseconds);
        Assert.IsFalse(File.Exists(evidence));
        Assert.IsEmpty(Directory.EnumerateFiles(
            temporary.FullName,
            "*.tmp",
            SearchOption.AllDirectories).ToArray());
    }

    [TestMethod]
    public async Task UnknownCommandAndChangedSdkFailWithoutEvidence()
    {
        using CSharpGateTemporaryDirectory temporary =
            new("program-kit-csharp-gate-invalid-");
        var project = await CreateBuildableProjectAsync(
            temporary.FullName,
            pause: false);
        var evidence = Path.Combine(temporary.FullName, "evidence.json");
        PinnedDotNetCSharpGateCompilerHarness sut = new();

        await Assert.ThrowsExactlyAsync<InvalidOperationException>(
            async () => await sut.VerifyAsync(
                Request(temporary.FullName, project, evidence) with
                {
                    Command = (CSharpGateCommand)999,
                },
                TestContext.CancellationToken));
        await Assert.ThrowsExactlyAsync<InvalidOperationException>(
            async () => await sut.VerifyAsync(
                Request(temporary.FullName, project, evidence) with
                {
                    DotNetSdkVersion = new SemanticVersion("10.0.999"),
                },
                TestContext.CancellationToken));
        Assert.IsFalse(File.Exists(evidence));
    }

    private static CSharpGateVerificationRequest Request(
        string root,
        string project,
        string evidence) =>
        new(
            root,
            project,
            CSharpGateCommand.Build,
            CSharpGateImplementationBoundary.WorkUnit,
            CSharpGateVerificationProfileKind.WorkUnit,
            new SemanticVersion("10.0.302"),
            evidence,
            [],
            [],
            [],
            1_048_576,
            60_000);

    private static async Task<string> CreateBuildableProjectAsync(
        string root,
        bool pause)
    {
        var project = Path.Combine(root, "Consumer.csproj");
        var target = pause
            ? """
              <Target Name="PauseForCancellation" BeforeTargets="CoreCompile">
                <Exec Command="powershell -NoProfile -Command &quot;Start-Sleep -Seconds 30&quot;" />
              </Target>
              """
            : string.Empty;
        await File.WriteAllTextAsync(
            project,
            $$"""
            <Project Sdk="Microsoft.NET.Sdk">
              <PropertyGroup>
                <TargetFramework>net10.0</TargetFramework>
                <OutputType>Exe</OutputType>
                <ImplicitUsings>enable</ImplicitUsings>
                <RestorePackagesWithLockFile>false</RestorePackagesWithLockFile>
              </PropertyGroup>
              {{target}}
            </Project>
            """);
        await File.WriteAllTextAsync(
            Path.Combine(root, "Program.cs"),
            "Console.WriteLine(\"verified\");");
        var restore = Run(root, "restore", project, "--nologo");
        Assert.AreEqual(0, restore.ExitCode, restore.Output);
        return project;
    }

    private static (int ExitCode, string Output) Run(
        string workingDirectory,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start dotnet.");
        var output = process.StandardOutput.ReadToEndAsync();
        var error = process.StandardError.ReadToEndAsync();
        process.WaitForExit();
        Task.WaitAll(output, error);
        return (
            process.ExitCode,
            string.Concat(output.Result, Environment.NewLine, error.Result));
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

        throw new DirectoryNotFoundException(
            "Could not find the Program Kit root.");
    }

}
