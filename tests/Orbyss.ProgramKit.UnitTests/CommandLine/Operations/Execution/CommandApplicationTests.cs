using System.Text;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Execution;

[TestClass]
public sealed class CommandApplicationTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task CapabilityBackendFailsWithCanonicalJsonDiagnostic()
    {
        TestCommandConsole console = new();
        var sut = CommandLineComposition.CreateDefault(console);

        var exitCode = await sut.RunAsync(
        [
            "capabilities",
            "verify-bundle",
            "bundle.json",
            "--diagnostics",
            "json",
        ],
        TestContext.CancellationToken);

        Assert.AreEqual(CommandExitCode.ConformanceFailure, exitCode);
        Assert.IsEmpty(console.StandardOutput);
        Assert.AreEqual(
            "{\"diagnostics\":[{\"id\":\"PKCLI007\",\"message\":\"The capability bundle must be supplied as one .nupkg file.\",\"path\":\"/bundle\",\"severity\":\"error\"}],\"exitCode\":1}",
            Encoding.UTF8.GetString(console.StandardError));
    }

    [TestMethod]
    public async Task NormalizeWritesCanonicalBytesToStandardOutput()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var input = Path.Combine(root, "input.json");
            await File.WriteAllBytesAsync(
                input,
                Encoding.UTF8.GetBytes("{\"z\":2,\"a\":1}"),
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var sut = CommandLineComposition.CreateDefault(console);

            var exitCode = await sut.RunAsync(
            [
                "normalize",
                input,
                "--output",
                "-",
            ],
            TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.Success, exitCode);
            Assert.AreEqual(
                "{\"a\":1,\"z\":2}",
                Encoding.UTF8.GetString(console.StandardOutput));
            Assert.IsEmpty(console.StandardError);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task DigestIsStableAcrossPropertyOrder()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var first = Path.Combine(root, "first.json");
            var second = Path.Combine(root, "second.json");
            await File.WriteAllBytesAsync(
                first,
                Encoding.UTF8.GetBytes("{\"z\":2,\"a\":1}"),
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                second,
                Encoding.UTF8.GetBytes("{\"a\":1,\"z\":2}"),
                TestContext.CancellationToken);
            TestCommandConsole firstConsole = new();
            TestCommandConsole secondConsole = new();
            var firstApplication = CommandLineComposition.CreateDefault(firstConsole);
            var secondApplication = CommandLineComposition.CreateDefault(secondConsole);

            var firstExit = await firstApplication.RunAsync(
                ["digest", first],
                TestContext.CancellationToken);
            var secondExit = await secondApplication.RunAsync(
                ["digest", second],
                TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.Success, firstExit);
            Assert.AreEqual(CommandExitCode.Success, secondExit);
            Assert.AreSequenceEqual(
                firstConsole.StandardOutput,
                secondConsole.StandardOutput);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task ValidateMapsSchemaFailureToConformanceExit()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var input = Path.Combine(root, "invalid-manifest.json");
            await File.WriteAllBytesAsync(
                input,
                Encoding.UTF8.GetBytes(
                    "{\"$schema\":\"pkid:schema:program-kit:dotnet-artifact-input-manifest@1.0.0\",\"version\":\"1.0.0\"}"),
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var sut = CommandLineComposition.CreateDefault(console);

            var exitCode = await sut.RunAsync(
                ["validate", input],
                TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.ConformanceFailure, exitCode);
            Assert.IsEmpty(console.StandardOutput);
            Assert.Contains("PKWB002", Encoding.UTF8.GetString(console.StandardError));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task InvalidJsonMapsToInputExitInsteadOfInternalFailure()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat("program-kit-cli-", Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var input = Path.Combine(root, "invalid.json");
            await File.WriteAllBytesAsync(
                input,
                "{"u8.ToArray(),
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var sut = CommandLineComposition.CreateDefault(console);

            var exitCode = await sut.RunAsync(
                ["digest", input],
                TestContext.CancellationToken);

            Assert.AreEqual(CommandExitCode.UsageOrInputFailure, exitCode);
            Assert.Contains(
                "PKCLI002",
                Encoding.UTF8.GetString(console.StandardError));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task NoArgumentsAndCommandHelpAreSuccessfulAndFinite()
    {
        TestCommandConsole firstUse = new();
        var firstApplication = CommandLineComposition.CreateDefault(firstUse);
        var firstExit = await firstApplication.RunAsync(
            [],
            TestContext.CancellationToken);
        TestCommandConsole commandHelp = new();
        var commandApplication =
            CommandLineComposition.CreateDefault(commandHelp);
        var commandExit = await commandApplication.RunAsync(
            ["capabilities", "initialize", "--help"],
            TestContext.CancellationToken);

        Assert.AreEqual(CommandExitCode.Success, firstExit);
        Assert.Contains(
            "capabilities initialize",
            Encoding.UTF8.GetString(firstUse.StandardOutput));
        Assert.AreEqual(CommandExitCode.Success, commandExit);
        var help = Encoding.UTF8.GetString(commandHelp.StandardOutput);
        Assert.Contains("--provider <claude|codex>", help);
        Assert.Contains("--workspace-root <value>", help);
        Assert.DoesNotContain("--program-kit-root", help);
    }

    [TestMethod]
    public async Task SchemaAndDiagnosticKnowledgeAreOfflineAndFinite()
    {
        TestCommandConsole schemaConsole = new();
        var schemaApplication =
            CommandLineComposition.CreateDefault(schemaConsole);
        var schemaExit = await schemaApplication.RunAsync(
        [
            "schemas",
            "read",
            "pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.2",
        ],
        TestContext.CancellationToken);
        TestCommandConsole diagnosticConsole = new();
        var diagnosticApplication =
            CommandLineComposition.CreateDefault(diagnosticConsole);
        var diagnosticExit = await diagnosticApplication.RunAsync(
            ["diagnostics", "explain", "CS1002", "--format", "json"],
            TestContext.CancellationToken);

        Assert.AreEqual(CommandExitCode.Success, schemaExit);
        Assert.Contains(
            "\"x-program-kit-version\": \"0.1.0-alpha.2\"",
            Encoding.UTF8.GetString(schemaConsole.StandardOutput));
        Assert.AreEqual(CommandExitCode.Success, diagnosticExit);
        var explanation =
            Encoding.UTF8.GetString(diagnosticConsole.StandardOutput);
        Assert.Contains("\"classification\":\"unregistered-external\"", explanation);
        Assert.Contains("\"owner\":\"C# compiler\"", explanation);
        Assert.DoesNotContain("Program Kit repair", explanation);
    }

    [TestMethod]
    public async Task GateMaterializerAcceptsOneBomAndWritesCanonicalBytes()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-gate-materializer-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            var source = Path.Combine(
                FindProgramKitRoot(),
                "extensions",
                "reusable-csharp-build-gates",
                "fixtures",
                "consumer-owned-build-gate-definition.json");
            var draft = Path.Combine(root, "draft.json");
            var output = Path.Combine(root, "definition.json");
            var sourceBytes = await File.ReadAllBytesAsync(
                source,
                TestContext.CancellationToken);
            await File.WriteAllBytesAsync(
                draft,
                [0xef, 0xbb, 0xbf, .. sourceBytes],
                TestContext.CancellationToken);
            TestCommandConsole console = new();
            var application = CommandLineComposition.CreateDefault(console);

            var exit = await application.RunAsync(
            [
                "csharp-gate",
                "materialize-definition",
                draft,
                "--output",
                output,
            ],
            TestContext.CancellationToken);

            Assert.AreEqual(
                CommandExitCode.Success,
                exit,
                Encoding.UTF8.GetString(console.StandardError));
            var outputBytes = await File.ReadAllBytesAsync(
                output,
                TestContext.CancellationToken);
            Assert.IsFalse(
                outputBytes.AsSpan().StartsWith(
                    [(byte)0xef, (byte)0xbb, (byte)0xbf]));
            Assert.StartsWith("{", Encoding.UTF8.GetString(outputBytes));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task ArtifactInspectionUsesAnExplicitRegisteredSchemaWithoutMutation()
    {
        var artifact = Path.Combine(
            FindProgramKitRoot(),
            "extensions",
            "reusable-csharp-build-gates",
            "fixtures",
            "consumer-owned-build-gate-definition.json");
        var before = await File.ReadAllBytesAsync(
            artifact,
            TestContext.CancellationToken);
        TestCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);

        var exit = await application.RunAsync(
        [
            "artifacts",
            "inspect",
            artifact,
            "--schema",
            "pkid:schema:program-kit:csharp-build-gate-definition@0.1.0-alpha.2",
            "--format",
            "json",
        ],
        TestContext.CancellationToken);
        var after = await File.ReadAllBytesAsync(
            artifact,
            TestContext.CancellationToken);

        Assert.AreEqual(CommandExitCode.Success, exit);
        Assert.Contains(
            "\"valid\":true",
            Encoding.UTF8.GetString(console.StandardOutput));
        Assert.AreSequenceEqual(before, after);
        Assert.IsEmpty(console.StandardError);
    }

    private static string FindProgramKitRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null &&
               !File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
        {
            current = current.Parent;
        }

        return current?.FullName ??
            throw new InvalidOperationException(
                "The Program Kit repository root was not found.");
    }
}
