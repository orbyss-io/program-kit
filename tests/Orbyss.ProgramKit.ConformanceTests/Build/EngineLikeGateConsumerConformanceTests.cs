using System.Diagnostics;
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.ConformanceTests.DotNet;

namespace Orbyss.ProgramKit.ConformanceTests.Build;

[TestClass]
[DoNotParallelize]
public sealed class EngineLikeGateConsumerConformanceTests
{
    private const string ConsumerAnalyzerProperty =
        "EngineConsumerAnalyzerPath";
    private const string PublicAnalyzerProperty =
        "ProgramKitPublicAnalyzerPath";

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task FictionalEngineLikeConsumerAdoptsExactLayeredGate()
    {
        var fixtureRoot = FixtureRoot();
        AssertFixtureAuthority(fixtureRoot);
        using TemporaryTestDirectory temporary =
            new("program-kit-engine-like-gate-consumer-");
        CopyDirectory(fixtureRoot, temporary.FullName);

        var analyzerProject = Path.Combine(
            temporary.FullName,
            "Analyzer",
            "Engine.Semantics.Analyzers.csproj");
        var analyzerRestore = await RunAsync(
            temporary.FullName,
            "restore",
            analyzerProject,
            "--locked-mode",
            "--ignore-failed-sources",
            "--nologo");
        Assert.AreEqual(0, analyzerRestore.ExitCode, analyzerRestore.Output);
        var analyzerBuild = await RunAsync(
            temporary.FullName,
            "build",
            analyzerProject,
            "--configuration",
            "Release",
            "--no-restore",
            "--nologo");
        Assert.AreEqual(0, analyzerBuild.ExitCode, analyzerBuild.Output);
        var consumerAnalyzer = Path.Combine(
            temporary.FullName,
            "Analyzer",
            "bin",
            "Release",
            "net10.0",
            "Engine.Semantics.Analyzers.dll");
        Assert.IsTrue(File.Exists(consumerAnalyzer), consumerAnalyzer);

        var publicAnalyzer = await BuildPublicAnalyzerAsync();
        var consumerProject = Path.Combine(
            temporary.FullName,
            "Consumer",
            "EngineLike.Consumer.csproj");
        var properties = AnalyzerProperties(
            consumerAnalyzer,
            publicAnalyzer);
        var restore = await RunAsync(
            temporary.FullName,
            [
                "restore",
                consumerProject,
                "--locked-mode",
                "--ignore-failed-sources",
                "--nologo",
                .. properties,
            ]);
        Assert.AreEqual(0, restore.ExitCode, restore.Output);

        var build = await OperationAsync(
            temporary.FullName,
            "build",
            consumerProject,
            properties);
        var test = await OperationAsync(
            temporary.FullName,
            "test",
            consumerProject,
            properties);
        var packageOutput = Path.Combine(temporary.FullName, "package");
        var pack = await RunAsync(
            temporary.FullName,
            [
                "pack",
                consumerProject,
                "--configuration",
                "Release",
                "--no-build",
                "--output",
                packageOutput,
                "--nologo",
                .. properties,
            ]);
        var publishOutput = Path.Combine(temporary.FullName, "publish");
        var publish = await RunAsync(
            temporary.FullName,
            [
                "publish",
                consumerProject,
                "--configuration",
                "Release",
                "--no-restore",
                "--output",
                publishOutput,
                "--nologo",
                .. properties,
            ]);

        Assert.AreEqual(0, build.ExitCode, build.Output);
        Assert.AreEqual(0, test.ExitCode, test.Output);
        Assert.AreEqual(0, pack.ExitCode, pack.Output);
        Assert.AreEqual(0, publish.ExitCode, publish.Output);

        var source = Path.Combine(
            temporary.FullName,
            "Consumer",
            "EngineKernel.cs");
        await File.WriteAllTextAsync(
            source,
            """
            namespace EngineLike.Consumer;

            public sealed class EngineService;
            """,
            Encoding.UTF8,
            TestContext.CancellationToken);
        var negative = await OperationAsync(
            temporary.FullName,
            "build",
            consumerProject,
            properties);
        Assert.AreNotEqual(0, negative.ExitCode, negative.Output);
        Assert.Contains("ENGINE0001", negative.Output);
        Assert.DoesNotContain("PKCC001", negative.Output);

        await File.WriteAllTextAsync(
            source,
            """
            namespace EngineLike.Consumer;

            public sealed class EngineKernel;
            """,
            Encoding.UTF8,
            TestContext.CancellationToken);
        var final = await OperationAsync(
            temporary.FullName,
            "build",
            consumerProject,
            properties);
        Assert.AreEqual(0, final.ExitCode, final.Output);

        var combinedOutput = string.Concat(
            build.Output,
            test.Output,
            pack.Output,
            publish.Output,
            negative.Output,
            final.Output);
        Assert.DoesNotContain("PKCS", combinedOutput);
        AssertReceiptClosure(temporary.FullName);
        AssertPackageClosure(packageOutput);
        AssertRuntimeClosure(
            Path.Combine(
                temporary.FullName,
                "Consumer",
                "bin",
                "Release",
                "net10.0"));
        AssertRuntimeClosure(publishOutput);
    }

    private static void AssertFixtureAuthority(string root)
    {
        using var manifest = JsonDocument.Parse(
            File.ReadAllBytes(Path.Combine(root, "fixture-manifest.json")));
        var value = manifest.RootElement;
        Assert.IsTrue(value.GetProperty("fictionalConsumer").GetBoolean());
        Assert.IsFalse(
            value.GetProperty("siblingRepositorySourceUsed").GetBoolean());
        Assert.IsFalse(
            value.GetProperty("consumerAnalyzer")
                .GetProperty("packable")
                .GetBoolean());
        Assert.IsFalse(
            value.GetProperty("authority")
                .GetProperty("generalCodeGenerator")
                .GetBoolean());
        Assert.IsTrue(
            value.GetProperty("authority")
                .GetProperty("narrowParticipationReceiptGenerator")
                .GetBoolean());

        var analyzerProject = File.ReadAllText(Path.Combine(
            root,
            "Analyzer",
            "Engine.Semantics.Analyzers.csproj"));
        Assert.Contains("<IsPackable>false</IsPackable>", analyzerProject);
        Assert.DoesNotContain("<PackageReference", analyzerProject);
        var ownership = File.ReadAllText(Path.Combine(
            root,
            "Analyzer",
            "gate",
            "ownership-manifest.json"));
        Assert.Contains(
            "\"recipeIdentity\": \"pkid:recipe:program-kit:forbid-type-name-suffix\"",
            ownership);
        Assert.Contains("\"diagnosticId\": \"ENGINE0001\"", ownership);
        var selections = File.ReadAllText(Path.Combine(
            root,
            "Analyzer",
            "gate",
            "public-analyzer-selections.json"));
        Assert.Contains(
            "\"componentIdentity\": \"pkid:analyzer:program-kit:generated-source-contract\"",
            selections);
        Assert.Contains("\"diagnosticIds\":", selections);
        Assert.Contains("\"PKCC001\"", selections);

        var sources = Directory.EnumerateFiles(
                Path.Combine(root, "Analyzer"),
                "*.cs",
                SearchOption.AllDirectories)
            .Select(File.ReadAllText)
            .ToArray();
        Assert.IsEmpty(sources.Where(source =>
            source.Contains("ISourceGenerator", StringComparison.Ordinal)));
        Assert.HasCount(
            1,
            sources.Where(source =>
                source.Contains(
                    "IIncrementalGenerator",
                    StringComparison.Ordinal) &&
                source.Contains(
                    "ParticipationReceipt",
                    StringComparison.Ordinal)));
        Assert.IsEmpty(Directory.EnumerateFiles(
                root,
                "*",
                SearchOption.AllDirectories)
            .Where(path => path.Contains(
                "Orbyss.ProgramKit.CSharpGate",
                StringComparison.OrdinalIgnoreCase)));

        using var fixtureLock = JsonDocument.Parse(
            File.ReadAllBytes(Path.Combine(root, "fixture-lock.json")));
        foreach (var input in fixtureLock.RootElement
                     .GetProperty("inputs")
                     .EnumerateArray())
        {
            var path = input.GetProperty("path").GetString()
                ?? throw new InvalidOperationException(
                    "Fixture lock paths cannot be null.");
            var actual = string.Concat(
                "sha256:",
                Convert.ToHexStringLower(
                    System.Security.Cryptography.SHA256.HashData(
                        File.ReadAllBytes(Path.Combine(
                            root,
                            path.Replace(
                                '/',
                                Path.DirectorySeparatorChar))))));
            Assert.AreEqual(
                input.GetProperty("digest").GetString(),
                actual,
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

    private static string[] AnalyzerProperties(
        string consumerAnalyzer,
        string publicAnalyzer) =>
        [
            string.Concat(
                "--property:",
                ConsumerAnalyzerProperty,
                "=",
                consumerAnalyzer),
            string.Concat(
                "--property:",
                PublicAnalyzerProperty,
                "=",
                publicAnalyzer),
        ];

    private static Task<(int ExitCode, string Output)> OperationAsync(
        string root,
        string operation,
        string project,
        string[] properties) =>
        RunAsync(
            root,
            [
                operation,
                project,
                "--configuration",
                "Release",
                "--no-restore",
                "--nologo",
                .. properties,
            ]);

    private static void AssertReceiptClosure(string root)
    {
        var receipts = Directory.EnumerateFiles(
                Path.Combine(root, "Consumer", "obj"),
                "*Receipt*.cs",
                SearchOption.AllDirectories)
            .Select(Path.GetFileName)
            .Distinct(StringComparer.Ordinal)
            .Order(StringComparer.Ordinal)
            .ToArray();
        Assert.HasCount(2, receipts);
        Assert.ContainsSingle(receipts.Where(name => name!.StartsWith(
            "Engine.Semantics.AnalyzersParticipationReceipt.",
            StringComparison.Ordinal)));
        Assert.ContainsSingle(receipts.Where(name => name!.StartsWith(
            "GeneratedSourceContractReceipt.",
            StringComparison.Ordinal)));
    }

    private static void AssertPackageClosure(string packageOutput)
    {
        var package = Directory.EnumerateFiles(
            packageOutput,
            "*.nupkg").Single();
        using var archive = ZipFile.OpenRead(package);
        Assert.IsEmpty(archive.Entries.Where(entry =>
            entry.FullName.Contains(
                "Analyzers",
                StringComparison.OrdinalIgnoreCase) ||
            entry.FullName.Contains(
                "ProgramKit",
                StringComparison.OrdinalIgnoreCase)));
    }

    private static void AssertRuntimeClosure(string path)
    {
        Assert.IsTrue(File.Exists(
            Path.Combine(path, "EngineLike.Consumer.dll")));
        Assert.IsFalse(File.Exists(Path.Combine(
            path,
            "Engine.Semantics.Analyzers.dll")));
        Assert.IsFalse(File.Exists(Path.Combine(
            path,
            "Orbyss.ProgramKit.GeneratedSourceContract.Analyzers.dll")));
        Assert.IsFalse(File.Exists(Path.Combine(
            path,
            "Orbyss.ProgramKit.CSharpGate.dll")));
    }

    private static string FixtureRoot() =>
        Path.Combine(
            ConformanceInputs.ProgramKitRoot,
            "tests",
            "Orbyss.ProgramKit.ConformanceTests",
            "Fixtures",
            "EngineLikeGateConsumer");

    private static void CopyDirectory(string source, string destination)
    {
        foreach (var directory in Directory.EnumerateDirectories(
                     source,
                     "*",
                     SearchOption.AllDirectories))
        {
            Directory.CreateDirectory(
                Path.Combine(
                    destination,
                    Path.GetRelativePath(source, directory)));
        }

        foreach (var file in Directory.EnumerateFiles(
                     source,
                     "*",
                     SearchOption.AllDirectories))
        {
            var target = Path.Combine(
                destination,
                Path.GetRelativePath(source, file));
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(file, target);
        }
    }

    private static async Task<(int ExitCode, string Output)> RunAsync(
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
        await process.WaitForExitAsync();
        return (
            process.ExitCode,
            string.Concat(
                await output,
                Environment.NewLine,
                await error));
    }
}
