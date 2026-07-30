using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.CommandLine.Composition;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.Planning.Plans;
using Orbyss.ProgramKit.UnitTests.CommandLine.Hosting.IO;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.Validation;

[TestClass]
public sealed class DesignFlowSchemaCommandTests
{
    private static readonly JsonSerializerOptions IndentedJson =
        new() { WriteIndented = true };

    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task CurrentDesignFlowWritersValidateThroughBothPublicPaths()
    {
        var temporaryRoot = CreateTemporaryRoot();
        try
        {
            var repositoryRoot = FindProgramKitRoot();
            var architecture = WriteCurrentWriter(
                Path.Combine(
                    repositoryRoot,
                    "extensions",
                    "alpha-version-transition",
                    "architecture-design.json"),
                Path.Combine(temporaryRoot, "architecture-design.json"),
                ArchitectureDesignDocumentAlpha3.SchemaUri,
                static root =>
                {
                    var domains = root["domains"]!.AsArray();
                    domains[0]!["identity"] =
                        "pkid:domain:program-kit:version.governance";
                });
            var disposition = WriteCurrentWriter(
                Path.Combine(
                    repositoryRoot,
                    "extensions",
                    "alpha-version-transition",
                    "static-conformance-disposition.json"),
                Path.Combine(temporaryRoot, "disposition.json"),
                StaticConformanceDispositionAlpha2.SchemaUri,
                static root =>
                {
                    var allocations = root["invariantAllocations"]!.AsArray();
                    allocations[0]!["identity"] =
                        "pkid:invariant:program-kit:alpha.transition-repository-source";
                });
            var plan = WriteCurrentWriter(
                Path.Combine(
                    repositoryRoot,
                    "extensions",
                    "alpha-version-transition",
                    "implementation-plan.json"),
                Path.Combine(temporaryRoot, "implementation-plan.json"),
                ImplementationPlanDocumentAlpha4.SchemaUri,
                static root =>
                    root["ownerId"] =
                        "pkid:approval-record:jtest:jtest-2.0");

            foreach (var artifact in new[] { architecture, disposition, plan })
            {
                await AssertValidAsync(["validate", artifact]);
                await AssertValidAsync(
                [
                    "artifacts",
                    "inspect",
                    artifact,
                    "--format",
                    "json",
                ]);
            }
        }
        finally
        {
            Directory.Delete(temporaryRoot, recursive: true);
        }
    }

    [TestMethod]
    public async Task LegacyDispositionRequiresExactExplicitSchemaSelection()
    {
        var artifact = Path.Combine(
            FindProgramKitRoot(),
            "extensions",
            "alpha-version-transition",
            "static-conformance-disposition.json");

        await AssertValidAsync(
        [
            "validate",
            artifact,
            "--schema",
            "pkid:schema:program-kit:static-conformance-disposition@0.1.0-alpha.1",
        ]);

        TestCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);
        var implicitExit = await application.RunAsync(
            ["validate", artifact],
            TestContext.CancellationToken);
        Assert.AreNotEqual(CommandExitCode.Success, implicitExit);
        Assert.IsNotEmpty(console.StandardError);
    }

    [TestMethod]
    public async Task IdentifierDiagnosticAndSchemaExposeTheSameExactGrammar()
    {
        TestCommandConsole diagnosticsConsole = new();
        var application = CommandLineComposition.CreateDefault(diagnosticsConsole);
        var diagnosticExit = await application.RunAsync(
        [
            "diagnostics",
            "explain",
            "PKART001",
            "--format",
            "text",
        ],
        TestContext.CancellationToken);
        Assert.AreEqual(CommandExitCode.Success, diagnosticExit);
        var explanation = Encoding.UTF8.GetString(
            diagnosticsConsole.StandardOutput);
        Assert.Contains(ProgramKitIdentifier.CanonicalPattern, explanation);
        Assert.Contains(
            "pkid:approval-record:jtest:jtest-2.0",
            explanation);

        TestCommandConsole schemaConsole = new();
        application = CommandLineComposition.CreateDefault(schemaConsole);
        var schemaExit = await application.RunAsync(
        [
            "schemas",
            "read",
            "pkid:schema:program-kit:artifact-definitions@0.1.0-alpha.2",
        ],
        TestContext.CancellationToken);
        Assert.AreEqual(CommandExitCode.Success, schemaExit);
        using var schema = JsonDocument.Parse(schemaConsole.StandardOutput);
        Assert.AreEqual(
            ProgramKitIdentifier.CanonicalPattern,
            schema.RootElement
                .GetProperty("$defs")
                .GetProperty("programKitIdentifier")
                .GetProperty("pattern")
                .GetString());
    }

    private async Task AssertValidAsync(string[] arguments)
    {
        TestCommandConsole console = new();
        var application = CommandLineComposition.CreateDefault(console);
        var exit = await application.RunAsync(
            arguments,
            TestContext.CancellationToken);
        Assert.AreEqual(
            CommandExitCode.Success,
            exit,
            Encoding.UTF8.GetString(console.StandardError));
        Assert.IsEmpty(console.StandardError);
    }

    private static string WriteCurrentWriter(
        string source,
        string destination,
        string schemaUri,
        Action<JsonObject> mutate)
    {
        var root = JsonNode.Parse(File.ReadAllBytes(source))!.AsObject();
        root["$schema"] = schemaUri;
        mutate(root);
        File.WriteAllBytes(
            destination,
            JsonSerializer.SerializeToUtf8Bytes(
                root,
                IndentedJson));
        return destination;
    }

    private static string CreateTemporaryRoot()
    {
        var path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-schema-flow-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
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
