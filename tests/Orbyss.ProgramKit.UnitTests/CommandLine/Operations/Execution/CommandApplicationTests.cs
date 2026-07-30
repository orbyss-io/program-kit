using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
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
    public async Task GateDescriptionPublishesExactLockAndTargetRules()
    {
        TestCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);

        var exit = await application.RunAsync(
        [
            "csharp-gate",
            "describe-definition",
            "--format",
            "json",
        ],
        TestContext.CancellationToken);

        Assert.AreEqual(
            CommandExitCode.Success,
            exit,
            Encoding.UTF8.GetString(console.StandardError));
        var output = Encoding.UTF8.GetString(console.StandardOutput);
        Assert.Contains(
            "projectProfileId|sourceProfileId|command|boundary|verificationProfile|comma-joined-analyzerComponentIds",
            output);
        Assert.Contains("cli-tests|... sorts before cli|...", output);
        Assert.Contains("\"inputDigest\"", output);
        Assert.Contains("\"outputDigest\"", output);
        Assert.Contains("ProgramKitVerifyGeneratedProject", output);
        Assert.Contains("csharp-gate scaffold-lock", output);
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

    [TestMethod]
    public async Task ConsoleContractDescriptionProjectsOneCatalogInTextAndJson()
    {
        TestCommandConsole textConsole = new();
        var textApplication = CommandLineComposition.CreateDefault(textConsole);
        var textExit = await textApplication.RunAsync(
        [
            "dotnet",
            "describe-console-contract",
            "--format",
            "text",
        ],
        TestContext.CancellationToken);
        TestCommandConsole jsonConsole = new();
        var jsonApplication = CommandLineComposition.CreateDefault(jsonConsole);
        var jsonExit = await jsonApplication.RunAsync(
        [
            "dotnet",
            "describe-console-contract",
            "--format",
            "json",
        ],
        TestContext.CancellationToken);

        Assert.AreEqual(CommandExitCode.Success, textExit);
        Assert.AreEqual(CommandExitCode.Success, jsonExit);
        var text = Encoding.UTF8.GetString(textConsole.StandardOutput);
        using var document = JsonDocument.Parse(jsonConsole.StandardOutput);
        var rules = document.RootElement.GetProperty("rules")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(5, rules);
        foreach (var rule in rules)
        {
            Assert.Contains(rule.GetProperty("id").GetString()!, text);
            Assert.Contains(rule.GetProperty("summary").GetString()!, text);
        }

        Assert.IsEmpty(textConsole.StandardError);
        Assert.IsEmpty(jsonConsole.StandardError);
    }

    [TestMethod]
    public async Task ConsoleRequestScaffoldIsDeterministicAndMatchesPackagedExample()
    {
        var root = CreateConsoleScaffoldRoot();
        try
        {
            var first = await RunConsoleScaffoldAsync(
                root,
                "request-one.json");
            var second = await RunConsoleScaffoldAsync(
                root,
                "request-two.json");

            Assert.AreEqual(CommandExitCode.Success, first.ExitCode);
            Assert.AreEqual(CommandExitCode.Success, second.ExitCode);
            var firstBytes = await File.ReadAllBytesAsync(
                Path.Combine(root, "request-one.json"),
                TestContext.CancellationToken);
            var secondBytes = await File.ReadAllBytesAsync(
                Path.Combine(root, "request-two.json"),
                TestContext.CancellationToken);
            var expected = await File.ReadAllBytesAsync(
                Path.Combine(
                    FindProgramKitRoot(),
                    "tests",
                    "Fixtures",
                    "ConsumerCliConsole",
                    "console-input-request-alpha2.json"),
                TestContext.CancellationToken);
            Assert.AreSequenceEqual(firstBytes, secondBytes);
            Assert.AreSequenceEqual(expected, firstBytes);
            Assert.IsFalse(
                firstBytes.AsSpan().StartsWith(
                    [(byte)0xef, (byte)0xbb, (byte)0xbf]));
            Assert.IsEmpty(first.StandardError);
            Assert.IsEmpty(second.StandardError);
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public async Task InitializedConsumerRetrievesExactConsoleExamples()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-console-resources-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        try
        {
            TestCommandConsole initializeConsole = new();
            var initializeApplication =
                CommandLineComposition.CreateDefault(initializeConsole);
            var initializeExit = await initializeApplication.RunAsync(
            [
                "capabilities",
                "initialize",
                "--provider",
                "codex",
                "--workspace-root",
                root,
            ],
            TestContext.CancellationToken);
            Assert.AreEqual(
                CommandExitCode.Success,
                initializeExit,
                Encoding.UTF8.GetString(initializeConsole.StandardError));

            var resources = new[]
            {
                (
                    Id: "dotnet-console-command-sketch-example",
                    Path:
                        ".agent-capabilities/supporting-resources/dotnet/dotnet-console-command-sketch-example.json"),
                (
                    Id: "dotnet-console-input-request-example",
                    Path:
                        ".agent-capabilities/supporting-resources/dotnet/dotnet-console-input-request-example.json"),
            };
            foreach (var resource in resources)
            {
                TestCommandConsole readConsole = new();
                var readApplication =
                    CommandLineComposition.CreateDefault(readConsole);
                var readExit = await readApplication.RunAsync(
                [
                    "capabilities",
                    "read-resource",
                    resource.Id,
                    "--workspace-root",
                    root,
                ],
                TestContext.CancellationToken);

                Assert.AreEqual(
                    CommandExitCode.Success,
                    readExit,
                    Encoding.UTF8.GetString(readConsole.StandardError));
                Assert.AreSequenceEqual(
                    await File.ReadAllBytesAsync(
                        Path.Combine(FindProgramKitRoot(), resource.Path),
                        TestContext.CancellationToken),
                    readConsole.StandardOutput);
            }
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    [DataRow("placeholder")]
    [DataRow("missing-semantics")]
    [DataRow("repeated-scalar")]
    [DataRow("stale-artifact")]
    [DataRow("bom")]
    [DataRow("escaping-project")]
    [DataRow("existing-output")]
    public async Task ConsoleRequestScaffoldRefusesInvalidOrOwnedInputs(
        string scenario)
    {
        var root = CreateConsoleScaffoldRoot();
        try
        {
            var sketch = Path.Combine(root, "console-command-sketch.json");
            var output = Path.Combine(root, "request.json");
            var consumerProject =
                "src/JTest.Console.Integration/JTest.Console.Integration.csproj";
            switch (scenario)
            {
                case "placeholder":
                    await MutateSketchAsync(
                        sketch,
                        static rootNode =>
                            rootNode["openConsole"]!["info"]!["summary"] =
                                "TODO");
                    break;
                case "missing-semantics":
                    await MutateSketchAsync(
                        sketch,
                        static rootNode =>
                            rootNode["openConsole"]!["commands"] =
                                new JsonArray());
                    break;
                case "repeated-scalar":
                    await MutateSketchAsync(
                        sketch,
                        static rootNode =>
                            rootNode["openConsole"]!["commands"]![0]![
                                "arguments"]![0]!["occurrence"]!["maximum"] = 2);
                    break;
                case "stale-artifact":
                    await File.AppendAllTextAsync(
                        Path.Combine(root, "inputs", "version-map.json"),
                        " ",
                        TestContext.CancellationToken);
                    break;
                case "bom":
                    var bytes = await File.ReadAllBytesAsync(
                        sketch,
                        TestContext.CancellationToken);
                    await File.WriteAllBytesAsync(
                        sketch,
                        [0xef, 0xbb, 0xbf, .. bytes],
                        TestContext.CancellationToken);
                    break;
                case "escaping-project":
                    consumerProject = "../outside.csproj";
                    break;
                case "existing-output":
                    await File.WriteAllTextAsync(
                        output,
                        "human-owned",
                        TestContext.CancellationToken);
                    break;
                default:
                    Assert.Fail(string.Concat("Unknown scenario: ", scenario));
                    break;
            }

            var result = await RunConsoleScaffoldAsync(
                root,
                "request.json",
                consumerProject);

            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                result.ExitCode);
            Assert.Contains("PKCIS001", result.StandardError);
            if (scenario == "placeholder")
            {
                Assert.Contains(
                    "/openConsole/info/summary",
                    result.StandardError);
            }
            Assert.IsFalse(File.Exists(
                string.Concat(output, ".program-kit-staging")));
            if (scenario == "existing-output")
            {
                Assert.AreEqual(
                    "human-owned",
                    await File.ReadAllTextAsync(
                        output,
                        TestContext.CancellationToken));
            }
            else
            {
                Assert.IsFalse(File.Exists(output));
            }
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private async Task<(
        CommandExitCode ExitCode,
        string StandardOutput,
        string StandardError)> RunConsoleScaffoldAsync(
        string root,
        string output,
        string consumerProject =
            "src/JTest.Console.Integration/JTest.Console.Integration.csproj")
    {
        TestCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);
        var exitCode = await application.RunAsync(
        [
            "dotnet",
            "scaffold-console-request",
            "console-command-sketch.json",
            "--workspace-root",
            root,
            "--consumer-project",
            consumerProject,
            "--output",
            output,
        ],
        TestContext.CancellationToken);
        return (
            exitCode,
            Encoding.UTF8.GetString(console.StandardOutput),
            Encoding.UTF8.GetString(console.StandardError));
    }

    private static string CreateConsoleScaffoldRoot()
    {
        var source = Path.Combine(
            FindProgramKitRoot(),
            "tests",
            "Fixtures",
            "ConsumerCliConsole");
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-console-scaffold-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(Path.Combine(root, "inputs"));
        Directory.CreateDirectory(
            Path.Combine(root, "src", "JTest.Console.Integration"));
        File.Copy(
            Path.Combine(source, "console-command-sketch.json"),
            Path.Combine(root, "console-command-sketch.json"));
        File.Copy(
            Path.Combine(source, "inputs", "version-map.json"),
            Path.Combine(root, "inputs", "version-map.json"));
        File.Copy(
            Path.Combine(source, "inputs", "version-selection.json"),
            Path.Combine(root, "inputs", "version-selection.json"));
        File.Copy(
            Path.Combine(
                source,
                "src",
                "JTest.Console.Integration",
                "JTest.Console.Integration.csproj"),
            Path.Combine(
                root,
                "src",
                "JTest.Console.Integration",
                "JTest.Console.Integration.csproj"));
        return root;
    }

    private static async Task MutateSketchAsync(
        string path,
        Action<JsonNode> mutation)
    {
        var root = JsonNode.Parse(await File.ReadAllBytesAsync(path)) ??
            throw new InvalidDataException("The fixture sketch is empty.");
        mutation(root);
        await File.WriteAllTextAsync(
            path,
            root.ToJsonString(),
            new UTF8Encoding(false));
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
