using System.Collections.Immutable;
using System.Diagnostics;
using System.Security;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Composition.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Selections;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Operations.Scaffolding;
using Orbyss.ProgramKit.ConformanceTests.DotNet;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
[DoNotParallelize]
public sealed class LayeredGateConsumerConformanceTests
{
    private const string Nonce = "0123456789abcdef0123456789abcdef";
    private static readonly string[] ExpectedCombinedDiagnostics =
        ["ACME0001", "PKCC001"];

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task PublicContractAndConsumerOwnedAnalyzersComposeWithoutLeakage()
    {
        AssertFixtureOwnership();
        using TemporaryTestDirectory temporary =
            new("program-kit-layered-gate-consumer-");
        var publicAnalyzer = await BuildPublicAnalyzerAsync();
        var consumerAnalyzer = await ScaffoldAndBuildConsumerAnalyzerAsync(
            temporary.FullName);

        var positive = BuildConsumer(
            Path.Combine(temporary.FullName, "positive"),
            publicAnalyzer,
            consumerAnalyzer,
            generatedHeader: true,
            consumerViolation: false,
            suppressConsumer: false);
        var publicNegative = BuildConsumer(
            Path.Combine(temporary.FullName, "public-negative"),
            publicAnalyzer,
            consumerAnalyzer,
            generatedHeader: false,
            consumerViolation: false,
            suppressConsumer: false);
        var consumerNegative = BuildConsumer(
            Path.Combine(temporary.FullName, "consumer-negative"),
            publicAnalyzer,
            consumerAnalyzer,
            generatedHeader: true,
            consumerViolation: true,
            suppressConsumer: false);
        var combinedNegative = BuildConsumer(
            Path.Combine(temporary.FullName, "combined-negative"),
            publicAnalyzer,
            consumerAnalyzer,
            generatedHeader: false,
            consumerViolation: true,
            suppressConsumer: false);
        var suppressed = BuildConsumer(
            Path.Combine(temporary.FullName, "suppressed"),
            publicAnalyzer,
            consumerAnalyzer,
            generatedHeader: true,
            consumerViolation: true,
            suppressConsumer: true);

        Assert.AreEqual(0, positive.ExitCode, positive.Output);
        Assert.AreNotEqual(0, publicNegative.ExitCode, publicNegative.Output);
        Assert.Contains("PKCC001", publicNegative.Output);
        Assert.DoesNotContain("ACME0001", publicNegative.Output);
        Assert.AreNotEqual(
            0,
            consumerNegative.ExitCode,
            consumerNegative.Output);
        Assert.Contains("ACME0001", consumerNegative.Output);
        Assert.DoesNotContain("PKCC001", consumerNegative.Output);
        Assert.AreSequenceEqual(
            ExpectedCombinedDiagnostics,
            Regex.Matches(
                    combinedNegative.Output,
                    @"(?:ACME\d{4}|PKCC\d{3})")
                .Select(static match => match.Value)
                .Distinct(StringComparer.Ordinal)
                .Order(StringComparer.Ordinal));
        Assert.AreEqual(0, suppressed.ExitCode, suppressed.Output);

        var receipts = Directory.EnumerateFiles(
                positive.ProjectDirectory,
                "*Receipt*.cs",
                SearchOption.AllDirectories)
            .Select(Path.GetFileName)
            .Order(StringComparer.Ordinal)
            .ToArray();
        Assert.HasCount(2, receipts);
        Assert.HasCount(
            1,
            receipts.Where(name => name!.StartsWith(
                "GeneratedSourceContractReceipt.",
                StringComparison.Ordinal)));
        Assert.HasCount(
            1,
            receipts.Where(name => name!.StartsWith(
                "Acme.Quality.AnalyzersParticipationReceipt.",
                StringComparison.Ordinal)));

        var runtime = Path.Combine(
            positive.ProjectDirectory,
            "bin",
            "Release",
            "net10.0");
        Assert.IsTrue(File.Exists(Path.Combine(runtime, "Consumer.dll")));
        Assert.IsFalse(File.Exists(Path.Combine(
            runtime,
            "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.dll")));
        Assert.IsFalse(File.Exists(Path.Combine(
            runtime,
            "Acme.Quality.Analyzers.dll")));
        Assert.DoesNotContain("PKCS", string.Concat(
            positive.Output,
            publicNegative.Output,
            consumerNegative.Output,
            combinedNegative.Output,
            suppressed.Output));
    }

    private static void AssertFixtureOwnership()
    {
        var root = Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "LayeredGateConsumer");
        using var manifest = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            root,
            "fixture-manifest.json")));
        var components = manifest.RootElement
            .GetProperty("components")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(2, components);
        Assert.AreEqual(
            "program-kit-public-contract",
            components[0].GetProperty("kind").GetString());
        Assert.AreEqual(
            "consumer-owned",
            components[1].GetProperty("kind").GetString());
        Assert.AreEqual(
            "pkid:domain:program-kit:generated-source-contract",
            components[0].GetProperty("semanticOwnerId").GetString());
        Assert.AreEqual(
            "pkid:owner:acme:quality",
            components[1].GetProperty("semanticOwnerId").GetString());

        var expected = File.ReadAllText(Path.Combine(
            root,
            "expected-evidence.json"));
        Assert.Contains("\"PKCC001\"", expected);
        Assert.Contains("\"ACME0001\"", expected);
        Assert.Contains("\"privateProgramKitPolicyExpected\": false", expected);
        Assert.DoesNotContain(ConformanceInputs.ProgramKitRoot, expected);

        using var fixtureLock = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(
            root,
            "fixture-lock.json")));
        foreach (var input in fixtureLock.RootElement
                     .GetProperty("inputs")
                     .EnumerateArray())
        {
            var path = input.GetProperty("path").GetString()
                ?? throw new InvalidOperationException(
                    "Fixture lock paths cannot be null.");
            var digest = string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(
                    File.ReadAllBytes(Path.Combine(root, path)))));
            Assert.AreEqual(
                input.GetProperty("digest").GetString(),
                digest,
                path);
        }
    }

    private static async Task<string> BuildPublicAnalyzerAsync()
    {
        var project = Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "src",
            "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers",
            "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.csproj");
        var build = await RunAsync(
            ConformanceInputs.ProgramKitRoot,
            "build",
            project,
            "--configuration",
            "Debug",
            "--no-restore",
            "--nologo");
        Assert.AreEqual(0, build.ExitCode, build.Output);
        var assembly = Path.Combine(
            Path.GetDirectoryName(project)!,
            "bin",
            "Debug",
            "net10.0",
            "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.dll");
        Assert.IsTrue(File.Exists(assembly), assembly);
        return assembly;
    }

    private async Task<string> ScaffoldAndBuildConsumerAnalyzerAsync(string root)
    {
        var output = Path.Combine(root, "Acme.Quality.Analyzers");
        ConsumerAnalyzerScaffoldingService service = new(
            new FileSystemConsumerAnalyzerScaffoldWorkspace());
        _ = await service.ScaffoldAsync(
            ScaffoldRequest(),
            output,
            TestContext.CancellationToken);
        var project = Path.Combine(output, "Acme.Quality.Analyzers.csproj");
        var build = await RunAsync(
            output,
            "build",
            project,
            "--configuration",
            "Release",
            "--nologo");
        Assert.AreEqual(0, build.ExitCode, build.Output);
        var assembly = Path.Combine(
            output,
            "bin",
            "Release",
            "net10.0",
            "Acme.Quality.Analyzers.dll");
        Assert.IsTrue(File.Exists(assembly), assembly);
        return assembly;
    }

    private static ConsumerAnalyzerScaffoldRequest ScaffoldRequest() =>
        new(
            "Acme.Quality.Analyzers",
            "Acme.Quality.Analyzers",
            new CSharpRuleRecipeBinding(
                CSharpRuleRecipeCatalog.ForbidTypeNameSuffix.Identity,
                CSharpRuleRecipeCatalog.ForbidTypeNameSuffix.Version,
                "pkid:owner:acme:quality",
                "pkid:rule:acme:forbid-service-suffix",
                "1.0.0",
                "ACME0001",
                "1.0.0",
                "Service suffix is forbidden",
                "Type name must not end with the consumer-selected suffix",
                ImmutableSortedDictionary<string, string>.Empty
                    .Add("forbiddenSuffix", "Service"),
                ["focused", "work-unit"],
                ["positive-type-name", "negative-service-name"],
                ["sdk:10.0.302", "roslyn:5.0.0", "language:14.0"],
                "source-local-ledger"),
            [
                new CSharpPublicAnalyzerSelectionProjection(
                    "pkid:analyzer:program-kit:generated-source-contract",
                    "pkid:domain:program-kit:generated-source-contract",
                    "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers",
                    "0.1.0-alpha.2",
                    new string('a', 64),
                    "analyzers/dotnet/cs/Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.dll",
                    new string('b', 64),
                    "pkid:contract:program-kit:generated-source-convention",
                    "1.0.0",
                    ["PKCC001"]),
            ]);

    private static LayeredBuildResult BuildConsumer(
        string root,
        string publicAnalyzer,
        string consumerAnalyzer,
        bool generatedHeader,
        bool consumerViolation,
        bool suppressConsumer)
    {
        Directory.CreateDirectory(root);
        var generated = Path.Combine(
            root,
            "ProgramKitGenerated",
            "Feature",
            "Generated.cs");
        Directory.CreateDirectory(Path.GetDirectoryName(generated)!);
        File.WriteAllText(
            generated,
            generatedHeader
                ? """
                  // <auto-generated program-kit>
                  namespace Consumer;
                  public sealed class GeneratedWidget;
                  """
                : """
                  namespace Consumer;
                  public sealed class GeneratedWidget;
                  """,
            Encoding.UTF8);
        var policy = consumerViolation
            ? suppressConsumer
                ? """
                  #pragma warning disable ACME0001
                  namespace Consumer;
                  public sealed class BillingService;
                  """
                : """
                  namespace Consumer;
                  public sealed class BillingService;
                  """
            : """
              namespace Consumer;
              public sealed class BillingProcessor;
              """;
        File.WriteAllText(
            Path.Combine(root, "Policy.cs"),
            policy,
            Encoding.UTF8);
        var project = Path.Combine(root, "Consumer.csproj");
        File.WriteAllText(
            project,
            $$"""
            <Project Sdk="Microsoft.NET.Sdk">
              <PropertyGroup>
                <TargetFramework>net10.0</TargetFramework>
                <LangVersion>14.0</LangVersion>
                <Nullable>enable</Nullable>
                <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
                <UseSharedCompilation>false</UseSharedCompilation>
                <EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>
                <CompilerGeneratedFilesOutputPath>obj\Generated</CompilerGeneratedFilesOutputPath>
                <ProgramKitGeneratedSourceContract>1.0.0</ProgramKitGeneratedSourceContract>
                <ProgramKitPublicAnalyzerReceiptNonce>{{Nonce}}</ProgramKitPublicAnalyzerReceiptNonce>
                <ProgramKitCompilerInvocationNonce>{{Nonce}}</ProgramKitCompilerInvocationNonce>
                <ProgramKitCSharpGateVerificationProfile>work-unit</ProgramKitCSharpGateVerificationProfile>
              </PropertyGroup>
              <ItemGroup>
                <Analyzer Include="{{SecurityElement.Escape(publicAnalyzer)}}" />
                <Analyzer Include="{{SecurityElement.Escape(consumerAnalyzer)}}" />
                <CompilerVisibleProperty Include="ProgramKitGeneratedSourceContract" />
                <CompilerVisibleProperty Include="ProgramKitPublicAnalyzerReceiptNonce" />
                <CompilerVisibleProperty Include="ProgramKitCompilerInvocationNonce" />
                <CompilerVisibleProperty Include="ProgramKitCSharpGateVerificationProfile" />
                <CompilerVisibleProperty Include="MSBuildProjectName" />
              </ItemGroup>
            </Project>
            """,
            Encoding.UTF8);
        var restore = Run(root, "restore", project, "--nologo");
        Assert.AreEqual(0, restore.ExitCode, restore.Output);
        var result = Run(
            root,
            "build",
            project,
            "--configuration",
            "Release",
            "--no-restore",
            "--nologo");
        return new LayeredBuildResult(
            result.ExitCode,
            result.Output,
            root);
    }

    private static async Task<(int ExitCode, string Output)> RunAsync(
        string workingDirectory,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = StartInfo(workingDirectory, arguments);
        using var process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start dotnet.");
        var output = process.StandardOutput.ReadToEndAsync();
        var error = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        return (
            process.ExitCode,
            string.Concat(
                await output,
                Environment.NewLine,
                await error));
    }

    private static (int ExitCode, string Output) Run(
        string workingDirectory,
        params string[] arguments)
    {
        ProcessStartInfo startInfo = StartInfo(workingDirectory, arguments);
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

    private static ProcessStartInfo StartInfo(
        string workingDirectory,
        IEnumerable<string> arguments)
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

        return startInfo;
    }

}
