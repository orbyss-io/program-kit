using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Materialization;

[TestClass]
public sealed class ConsoleInputMaterializerTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task CheckedInColdConsumerRequestMatchesCanonicalProjection()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            _ = await WriteRequestAsync(root, CreateSerializer());
            var fixtureRoot = GetColdConsumerFixtureRoot();

            foreach (var relativePath in new[]
                     {
                         "console-input-request.json",
                         "inputs/version-map.json",
                         "inputs/version-selection.json",
                     })
            {
                Assert.AreSequenceEqual(
                    await File.ReadAllBytesAsync(
                        Path.Combine(root, relativePath),
                        TestContext.CancellationToken),
                    await File.ReadAllBytesAsync(
                        Path.Combine(fixtureRoot, relativePath),
                        TestContext.CancellationToken),
                    relativePath);
            }
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task MaterializationCreatesAndThenRetainsOneExactClosure()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(
                root,
                serializer);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location);
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);
            var output = Path.Combine(root, ".program-kit", "console-inputs");

            var created = await materializer.MaterializeAsync(
                requestPath,
                root,
                output,
                CancellationToken.None);
            var unchanged = await materializer.MaterializeAsync(
                requestPath,
                root,
                output,
                CancellationToken.None);

            Assert.AreEqual(
                ConsoleInputMaterializationStatus.Created,
                created.Status);
            Assert.AreEqual(
                ConsoleInputMaterializationStatus.Unchanged,
                unchanged.Status);
            Assert.IsTrue(File.Exists(Path.Combine(output, "shell.json")));
            Assert.IsTrue(File.Exists(
                Path.Combine(output, "open-console.json")));
            Assert.IsTrue(File.Exists(
                Path.Combine(output, "console-binding.json")));
            Assert.IsTrue(File.Exists(
                Path.Combine(output, "artifact-manifest.json")));
            Assert.IsTrue(File.Exists(Path.Combine(
                output,
                ".program-kit-console-inputs.lock.json")));
            var reference = Directory.GetFiles(
                Path.Combine(output, "references"),
                "*.dll",
                SearchOption.AllDirectories).Single();
            Assert.IsTrue(
                File.GetAttributes(reference)
                    .HasFlag(FileAttributes.ReadOnly));
            Assert.HasCount(4, runner.Requests);
            Assert.Contains(
                "--no-restore",
                runner.Requests[0].Arguments);
            Assert.AreEqual("msbuild", runner.Requests[1].Arguments[0]);
            Assert.Contains(
                "-target:FindReferenceAssembliesForReferences",
                runner.Requests[1].Arguments);
            Assert.Contains(
                "-getProperty:TargetPath",
                runner.Requests[1].Arguments);
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task BuildFailurePromotesNoProgramKitOutput()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(
                root,
                serializer);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location,
                buildExitCode: 1);
            var output = Path.Combine(root, ".program-kit", "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        CancellationToken.None));

            Assert.AreEqual("PKCIM003", exception.DiagnosticId);
            Assert.IsFalse(Directory.Exists(output));
            Assert.IsFalse(Directory.Exists(
                string.Concat(output, ".program-kit-transaction")));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task AuthoringWorkspaceIsRejectedBeforeBuildOrWrite()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var requestPath = await WriteRequestAsync(
                root,
                CreateSerializer());
            var markerRoot = Path.Combine(
                root,
                ".agent-capabilities");
            Directory.CreateDirectory(markerRoot);
            await File.WriteAllTextAsync(
                Path.Combine(markerRoot, "authoring-workspace.json"),
                "{}",
                TestContext.CancellationToken);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                CreateSerializer());

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM009", exception.DiagnosticId);
            Assert.IsEmpty(runner.Requests);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    [DataRow(",\"unknown\":true}")]
    [DataRow(",\"version\":\"0.1.0-alpha.1\"}")]
    public async Task UnknownOrDuplicateRequestPropertiesFailBeforeBuild(
        string suffix)
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var requestPath = await WriteRequestAsync(
                root,
                CreateSerializer());
            var request = await File.ReadAllTextAsync(
                requestPath,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                requestPath,
                string.Concat(request.AsSpan(0, request.Length - 1), suffix),
                TestContext.CancellationToken);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                CreateSerializer());

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM001", exception.DiagnosticId);
            Assert.IsEmpty(runner.Requests);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task StrictReadFailureReportsDeepRequestMemberAndType()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(root, serializer);
            var request = await File.ReadAllTextAsync(
                requestPath,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                requestPath,
                request.Replace(
                    "\"generatedSymbol\":\"Run\"",
                    "\"generatedSymbol\":false",
                    StringComparison.Ordinal),
                TestContext.CancellationToken);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM001", exception.DiagnosticId);
            Assert.AreEqual(
                "/request/binding/operations/0/generatedSymbol",
                exception.Path);
            Assert.Contains(
                "Member 'generatedSymbol'",
                exception.Message);
            Assert.Contains(
                "expected CLR type 'System.String'",
                exception.Message);
            Assert.IsEmpty(runner.Requests);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task StaleSuppliedArtifactPromotesNoOutput()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(root, serializer);
            await File.WriteAllTextAsync(
                Path.Combine(root, "inputs", "version-map.json"),
                "{\"changed\":true}",
                TestContext.CancellationToken);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM001", exception.DiagnosticId);
            Assert.HasCount(2, runner.Requests);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task EscapingConsumerProjectPathFailsBeforeBuildOrWrite()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(root, serializer);
            var request = await File.ReadAllTextAsync(
                requestPath,
                TestContext.CancellationToken);
            await File.WriteAllTextAsync(
                requestPath,
                request.Replace(
                    "src/JTest.Console.Integration/JTest.Console.Integration.csproj",
                    "../outside.csproj",
                    StringComparison.Ordinal),
                TestContext.CancellationToken);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM001", exception.DiagnosticId);
            Assert.IsEmpty(runner.Requests);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task MissingEvaluatedReferencePromotesNoOutput()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(root, serializer);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location,
                compilationReferencePaths:
                [
                    Path.Combine(root, "missing-reference.dll"),
                ]);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM005", exception.DiagnosticId);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task DuplicateEvaluatedReferencePromotesNoOutput()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(root, serializer);
            var reference = typeof(JTestRunRequest).Assembly.Location;
            var runner = new RecordingConsoleMaterializationRunner(
                reference,
                compilationReferencePaths: [reference, reference]);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM005", exception.DiagnosticId);
            Assert.IsFalse(Directory.Exists(output));
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    [TestMethod]
    public async Task ModifiedOwnedOutputIsRefusedBeforeAnotherBuild()
    {
        var root = CreateRoot();
        CommandFileSystem fileSystem = new();
        try
        {
            var serializer = CreateSerializer();
            var requestPath = await WriteRequestAsync(root, serializer);
            var runner = new RecordingConsoleMaterializationRunner(
                typeof(JTestRunRequest).Assembly.Location);
            var output = Path.Combine(
                root,
                ".program-kit",
                "console-inputs");
            var materializer = CreateMaterializer(
                fileSystem,
                runner,
                serializer);
            _ = await materializer.MaterializeAsync(
                requestPath,
                root,
                output,
                TestContext.CancellationToken);
            await File.AppendAllTextAsync(
                Path.Combine(output, "shell.json"),
                "tampered",
                TestContext.CancellationToken);

            var exception =
                await Assert.ThrowsAsync<ConsoleInputMaterializationException>(
                    async () => await materializer.MaterializeAsync(
                        requestPath,
                        root,
                        output,
                        TestContext.CancellationToken));

            Assert.AreEqual("PKCIM007", exception.DiagnosticId);
            Assert.HasCount(2, runner.Requests);
        }
        finally
        {
            fileSystem.DeleteDirectory(root);
        }
    }

    private static ConsoleInputMaterializer CreateMaterializer(
        ICommandFileSystem fileSystem,
        RecordingConsoleMaterializationRunner runner,
        IProgramKitJsonSerializer serializer) =>
        new(
            fileSystem,
            runner,
            serializer,
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator(),
                new TransportFailureProfileValidator(),
                new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
                DotNetTestContractFactory.ProviderCatalog()),
            new OpenConsoleDocumentValidator(),
            new DotNetConsoleBindingValidator(),
            new DotNetConsoleMetadataInspector(),
            new DotNetConsoleIntegrationAssemblyInspector());

    private static async Task<string> WriteRequestAsync(
        string root,
        ProgramKitJsonSerializer serializer)
    {
        var inputRoot = Path.Combine(root, "inputs");
        Directory.CreateDirectory(inputRoot);
        var mapBytes = "{}"u8.ToArray();
        var selectionBytes = "[]"u8.ToArray();
        await File.WriteAllBytesAsync(
            Path.Combine(inputRoot, "version-map.json"),
            mapBytes);
        await File.WriteAllBytesAsync(
            Path.Combine(inputRoot, "version-selection.json"),
            selectionBytes);
        var mapRevision = Revision("version-map", mapBytes);
        var selectionRevision = Revision(
            "version-selection",
            selectionBytes);
        var shell = DotNetTestContractFactory.Shell() with
        {
            InputVersionMapRevision = mapRevision,
            InputVersionSelectionRevision = selectionRevision,
        };
        var document = DotNetTestContractFactory.JTestConsoleDocument(shell);
        var consoleHost = shell.Hosts.Single(static host =>
            host.Kind == DotNetHostKind.Console);
        var templateBinding = consoleHost.OperationBindings.Single();
        consoleHost = consoleHost with
        {
            OperationBindings = document.Commands
                .Select(command => templateBinding with
                {
                    OperationContract =
                        templateBinding.OperationContract with
                        {
                            OperationRevision =
                                command.OperationRevision,
                        },
                })
                .ToImmutableArray(),
        };
        shell = shell with
        {
            Hosts = shell.Hosts
                .Select(host => host.Kind == DotNetHostKind.Console
                    ? consoleHost
                    : host)
                .ToImmutableArray(),
        };
        document = DotNetTestContractFactory.JTestConsoleDocument(shell);
        var binding = DotNetConsoleBindingTestFactory
            .JTestGenerationInput(
                document,
                DotNetTestContractFactory.Ref(
                    "document",
                    "jtest-console",
                    '1'))
            .Binding;
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Console);
        var request = new DotNetConsoleInputMaterializationRequest(
            "pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.1",
            new SemanticVersion("0.1.0-alpha.1"),
            new ProgramKitIdentifier(
                "pkid:request:consumer:console-inputs"),
            new ProgramKitIdentifier(
                "pkid:component:consumer:jtest"),
            new ProgramKitIdentifier(
                "pkid:output-set:consumer:console-inputs"),
            host.Identity,
            "src/JTest.Console.Integration/JTest.Console.Integration.csproj",
            binding.ConsumerProject.Identity,
            binding.ConsumerProject.Name,
            "net10.0",
            "Release",
            "AnyCPU",
            shell,
            new DotNetConsoleOpenConsoleIntent(
                document.Schema,
                document.DocumentVersion,
                document.Info,
                document.HostRevision,
                document.Parsing,
                document.HostExitCodeRoles,
                document.GlobalOptions,
                document.Commands,
                document.Help,
                document.Completion,
                document.Compatibility,
                document.Provenance.GeneratorRevision,
                document.Provenance.OperationRevisions),
            new DotNetConsoleBindingIntent(
                binding.Schema,
                binding.Version,
                binding.FeatureType,
                binding.ValidationResultType,
                binding.Operations),
            [
                new DotNetConsoleSuppliedArtifact(
                    mapRevision,
                    "inputs/version-map.json",
                    "versions/version-map.json"),
                new DotNetConsoleSuppliedArtifact(
                    selectionRevision,
                    "inputs/version-selection.json",
                    "versions/version-selection.json"),
            ]);
        var requestPath = Path.Combine(root, "console-input-request.json");
        var bytes = serializer.Write(
            request,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            JsonSerializationLimits.Default);
        await File.WriteAllBytesAsync(requestPath, bytes.ToArray());
        return requestPath;
    }

    private static ArtifactReference Revision(
        string name,
        ReadOnlySpan<byte> bytes) =>
        new(
            new ProgramKitIdentifier(
                string.Concat("pkid:artifact:consumer:", name)),
            new SemanticVersion("0.1.0-alpha.1"),
            new Sha256Digest(
                string.Concat(
                    "sha256:",
                    Convert.ToHexStringLower(SHA256.HashData(bytes)))));

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder builder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(builder);
        return new ProgramKitJsonSerializer(
            builder.Freeze(),
            new ProgramKitJsonCanonicalizer());
    }

    private static string CreateRoot()
    {
        var root = Path.Combine(
            Path.GetTempPath(),
            string.Concat(
                "program-kit-console-materialization-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(root);
        return root;
    }

    private static string GetColdConsumerFixtureRoot() =>
        Path.GetFullPath(
            Path.Combine(
                AppContext.BaseDirectory,
                "..",
                "..",
                "..",
                "..",
                "..",
                "tests",
                "Fixtures",
                "ConsumerCliConsole"));
}
