using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;
using Orbyss.ProgramKit.CommandLine.Operations.Files;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Clients;

[TestClass]
public sealed class KiotaForeignClientGeneratorTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task ExactLocalInputGeneratesDeterministicIsolatedTree()
    {
        var root = TemporaryRoot();
        try
        {
            var input = Path.Combine(root, "foreign.openapi.json");
            await File.WriteAllTextAsync(
                input,
                OpenApi("widgets"),
                TestContext.CancellationToken);
            RecordingKiotaRunner runner = new();
            RecordingKiotaToolPackageMaterializer materializer = new();
            KiotaForeignClientGenerator generator =
                new(new CommandFileSystem(), runner, materializer);

            var first = await generator.GenerateAsync(
                Request(input, Path.Combine(root, "first")),
                TestContext.CancellationToken);
            var second = await generator.GenerateAsync(
                Request(input, Path.Combine(root, "second")),
                TestContext.CancellationToken);

            Assert.AreEqual(first.InputDigest, second.InputDigest);
            Assert.AreEqual(first.LockDigest, second.LockDigest);
            Assert.AreEqual(
                first.GeneratedTreeDigest,
                second.GeneratedTreeDigest);
            Assert.AreSequenceEqual(first.Files, second.Files);
            Assert.HasCount(8, first.RuntimeDependencies);
            Assert.IsTrue(first.Files.Any(static file =>
                file.RelativePath == "kiota-lock.json"));
            Assert.IsTrue(first.Files.Any(static file =>
                file.RelativePath == "program-kit.client-generation.json"));
            Assert.IsTrue(first.Files.Any(static file =>
                file.RelativePath.EndsWith(".cs", StringComparison.Ordinal)));
            Assert.IsTrue(runner.Requests.All(static request =>
                request.Executable == "dotnet" &&
                request.Arguments[0].EndsWith(
                    "kiota.dll",
                    StringComparison.Ordinal) &&
                request.Environment.ContainsKey("DOTNET_CLI_HOME") &&
                request.Environment.ContainsKey("TEMP")));
            Assert.HasCount(2, materializer.Requests);
            Assert.IsTrue(runner.Requests
                .Where(static request =>
                    request.Arguments.Contains("generate"))
                .All(static request =>
                    request.Arguments.Contains("--clean-output") &&
                    request.Arguments.Contains(
                        "--exclude-backward-compatible") &&
                    Path.GetFileName(request.WorkingDirectory).StartsWith(
                        ".program-kit-kiota-",
                        StringComparison.Ordinal)));
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    [TestMethod]
    public async Task ChangedInputChangesInputLockAndTreeEvidence()
    {
        var root = TemporaryRoot();
        try
        {
            var firstInput = Path.Combine(root, "first.openapi.json");
            var secondInput = Path.Combine(root, "second.openapi.json");
            await File.WriteAllTextAsync(
                firstInput,
                OpenApi("widgets"),
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                secondInput,
                OpenApi("gadgets"),
                TestContext.CancellationToken);
            KiotaForeignClientGenerator generator =
                new(
                    new CommandFileSystem(),
                    new RecordingKiotaRunner(),
                    new RecordingKiotaToolPackageMaterializer());

            var first = await generator.GenerateAsync(
                Request(firstInput, Path.Combine(root, "first")),
                TestContext.CancellationToken);
            var second = await generator.GenerateAsync(
                Request(secondInput, Path.Combine(root, "second")),
                TestContext.CancellationToken);

            Assert.AreNotEqual(first.InputDigest, second.InputDigest);
            Assert.AreNotEqual(first.LockDigest, second.LockDigest);
            Assert.AreNotEqual(
                first.GeneratedTreeDigest,
                second.GeneratedTreeDigest);
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    [TestMethod]
    public async Task ChangedOptionChangesLockAndTreeEvidence()
    {
        var root = TemporaryRoot();
        try
        {
            var input = Path.Combine(root, "foreign.openapi.json");
            await File.WriteAllTextAsync(
                input,
                OpenApi("widgets"),
                TestContext.CancellationToken);
            KiotaForeignClientGenerator generator =
                new(
                    new CommandFileSystem(),
                    new RecordingKiotaRunner(),
                    new RecordingKiotaToolPackageMaterializer());

            var first = await generator.GenerateAsync(
                Request(input, Path.Combine(root, "first")),
                TestContext.CancellationToken);
            var second = await generator.GenerateAsync(
                Request(
                    input,
                    Path.Combine(root, "second"),
                    "Orbyss.ProgramKit.Alternate",
                    "AlternateClient"),
                TestContext.CancellationToken);

            Assert.AreEqual(first.InputDigest, second.InputDigest);
            Assert.AreNotEqual(first.LockDigest, second.LockDigest);
            Assert.AreNotEqual(
                first.GeneratedTreeDigest,
                second.GeneratedTreeDigest);
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    [TestMethod]
    public async Task ExternalReferenceFailsBeforeToolInvocation()
    {
        var root = TemporaryRoot();
        try
        {
            var input = Path.Combine(root, "foreign.openapi.json");
            await File.WriteAllTextAsync(
                input,
                """
                {
                  "openapi": "3.0.3",
                  "paths": {},
                  "components": {
                    "schemas": {
                      "Remote": {
                        "$ref": "https://example.invalid/remote.json"
                      }
                    }
                  }
                }
                """,
                TestContext.CancellationToken);
            RecordingKiotaRunner runner = new();
            KiotaForeignClientGenerator generator =
                new(
                    new CommandFileSystem(),
                    runner,
                    new RecordingKiotaToolPackageMaterializer());

            var exception = await Assert.ThrowsAsync<KiotaGenerationException>(
                async () => await generator.GenerateAsync(
                    Request(input, Path.Combine(root, "output")),
                    TestContext.CancellationToken));

            Assert.AreEqual(
                KiotaGenerationDiagnosticIds.InvalidInput,
                exception.DiagnosticId);
            Assert.AreEqual(
                CommandExitCode.UsageOrInputFailure,
                exception.ExitCode);
            Assert.IsEmpty(runner.Requests);
            Assert.IsFalse(Directory.Exists(Path.Combine(root, "output")));
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    [TestMethod]
    public async Task MalformedOpenApiFailsBeforeToolInvocation()
    {
        var root = TemporaryRoot();
        try
        {
            var input = Path.Combine(root, "foreign.openapi.json");
            await File.WriteAllTextAsync(
                input,
                """{"openapi":"3.0.3","paths":""",
                TestContext.CancellationToken);
            RecordingKiotaRunner runner = new();
            KiotaForeignClientGenerator generator =
                new(
                    new CommandFileSystem(),
                    runner,
                    new RecordingKiotaToolPackageMaterializer());

            var exception = await Assert.ThrowsAsync<KiotaGenerationException>(
                async () => await generator.GenerateAsync(
                    Request(input, Path.Combine(root, "output")),
                    TestContext.CancellationToken));

            Assert.AreEqual(
                KiotaGenerationDiagnosticIds.InvalidInput,
                exception.DiagnosticId);
            Assert.IsEmpty(runner.Requests);
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    [TestMethod]
    public async Task ToolFailureRemovesPartialStagingAndPublishesNothing()
    {
        var root = TemporaryRoot();
        try
        {
            var input = Path.Combine(root, "foreign.openapi.json");
            await File.WriteAllTextAsync(
                input,
                OpenApi("widgets"),
                TestContext.CancellationToken);
            KiotaForeignClientGenerator generator =
                new(
                    new CommandFileSystem(),
                    new RecordingKiotaRunner(true),
                    new RecordingKiotaToolPackageMaterializer());
            var output = Path.Combine(root, "output");

            var exception = await Assert.ThrowsAsync<KiotaGenerationException>(
                async () => await generator.GenerateAsync(
                    Request(input, output),
                    TestContext.CancellationToken));

            Assert.AreEqual(
                KiotaGenerationDiagnosticIds.ToolFailure,
                exception.DiagnosticId);
            Assert.AreEqual(
                CommandExitCode.ConformanceFailure,
                exception.ExitCode);
            Assert.IsFalse(Directory.Exists(output));
            Assert.IsEmpty(Directory
                .EnumerateDirectories(root)
                .Where(static path =>
                    Path.GetFileName(path).StartsWith(
                        ".program-kit-kiota-",
                        StringComparison.Ordinal)));
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    [TestMethod]
    public async Task CancellationRemovesPartialStagingAndPublishesNothing()
    {
        var root = TemporaryRoot();
        try
        {
            var input = Path.Combine(root, "foreign.openapi.json");
            await File.WriteAllTextAsync(
                input,
                OpenApi("widgets"),
                TestContext.CancellationToken);
            KiotaForeignClientGenerator generator =
                new(
                    new CommandFileSystem(),
                    new RecordingKiotaRunner(cancelGeneration: true),
                    new RecordingKiotaToolPackageMaterializer());
            var output = Path.Combine(root, "output");

            _ = await Assert.ThrowsAsync<OperationCanceledException>(
                async () => await generator.GenerateAsync(
                    Request(input, output),
                    TestContext.CancellationToken));

            Assert.IsFalse(Directory.Exists(output));
            Assert.IsEmpty(Directory
                .EnumerateDirectories(root)
                .Where(static path =>
                    Path.GetFileName(path).StartsWith(
                        ".program-kit-kiota-",
                        StringComparison.Ordinal)));
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    [TestMethod]
    public async Task PartialSuccessfulOutputWithoutLockFailsClosed()
    {
        var root = TemporaryRoot();
        try
        {
            var input = Path.Combine(root, "foreign.openapi.json");
            await File.WriteAllTextAsync(
                input,
                OpenApi("widgets"),
                TestContext.CancellationToken);
            KiotaForeignClientGenerator generator =
                new(
                    new CommandFileSystem(),
                    new RecordingKiotaRunner(omitLock: true),
                    new RecordingKiotaToolPackageMaterializer());
            var output = Path.Combine(root, "output");

            var exception = await Assert.ThrowsAsync<KiotaGenerationException>(
                async () => await generator.GenerateAsync(
                    Request(input, output),
                    TestContext.CancellationToken));

            Assert.AreEqual(
                KiotaGenerationDiagnosticIds.LockMismatch,
                exception.DiagnosticId);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            DeleteTemporaryRoot(root);
        }
    }

    private static KiotaForeignClientGenerationRequest Request(
        string input,
        string output,
        string namespaceName = "Orbyss.ProgramKit.ForeignApi",
        string className = "ForeignApiClient") =>
        new(
            input,
            output,
            Path.Combine(FindProgramKitRoot(), ".config", "dotnet-tools.json"),
            Path.Combine(FindProgramKitRoot(), "kiota-tool.nupkg"),
            namespaceName,
            className,
            [],
            []);

    private static string OpenApi(string resource) =>
        $$"""
        {
          "openapi": "3.0.3",
          "info": {
            "title": "Foreign API",
            "version": "1.0.0"
          },
          "paths": {
            "/{{resource}}": {
              "get": {
                "operationId": "get{{resource}}",
                "responses": {
                  "204": {
                    "description": "No content."
                  }
                }
              }
            }
          }
        }
        """;

    private static string TemporaryRoot()
    {
        var path = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-kiota-unit-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(path);
        return path;
    }

    private static void DeleteTemporaryRoot(string root)
    {
        var fullRoot = Path.GetFullPath(root);
        var temporaryRoot = Path.GetFullPath(Path.GetTempPath());
        Assert.IsTrue(
            fullRoot.StartsWith(
                temporaryRoot,
                OperatingSystem.IsWindows()
                    ? StringComparison.OrdinalIgnoreCase
                    : StringComparison.Ordinal));
        if (Directory.Exists(fullRoot))
        {
            Directory.Delete(fullRoot, recursive: true);
        }
    }

    private static string FindProgramKitRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(
                    current.FullName,
                    ".config",
                    "dotnet-tools.json")))
            {
                return current.FullName;
            }

            current = current.Parent;
        }

        throw new InvalidOperationException(
            "Could not locate the Program Kit root.");
    }

}
