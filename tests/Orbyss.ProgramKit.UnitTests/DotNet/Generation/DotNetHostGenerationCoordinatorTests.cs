using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetHostGenerationCoordinatorTests
{
    [TestMethod]
    public async Task ConsoleGenerationBindsExactShellLockHostAndDocumentProjection()
    {
        var shell = DotNetTestContractFactory.Shell();
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "reviewed",
            '6');
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Console);
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        var lockDocument = CreateLock(shell, shellRevision);
        var coordinator = CreateCoordinator();
        ConsoleHostGenerator sut = new(coordinator);
        var documentRevision = DocumentRevision(document);
        var input = new DotNetHostGenerationInput(
            shell,
            shellRevision,
            lockDocument,
            host.Identity,
            null,
            document,
            null,
            documentRevision,
            DotNetConsoleBindingTestFactory.GenerationInput(
                document,
                documentRevision));

        var outputs = await sut.GenerateAsync(
            input,
            CancellationToken.None);

        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "GeneratedHost.csproj"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "ProgramKitGenerated/Commands/ObserveRun/ObserveRunSettings.cs"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "ProgramKitGenerated/Commands/ObserveRun/ObserveRunCommand.cs"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "ProgramKitGenerated/Commands/ObserveRun/ObserveRunRequestFactory.cs"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "ProgramKitGenerated/Program.cs"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "docs/open-console.json"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "shell.lock.json"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "docs/dotnet-console-binding.json"));
        Assert.IsFalse(outputs.Any(static output =>
            output.RelativePath.Contains(
                "Dispatcher",
                StringComparison.Ordinal)));
        Assert.IsFalse(outputs.Any(static output =>
            output.RelativePath.Contains(
                "Parser",
                StringComparison.Ordinal)));
        var project = Text(outputs, "GeneratedHost.csproj");
        Assert.Contains(
            "<PackageReference Include=\"Spectre.Console.Cli\" Version=\"[0.55.0]\" />",
            project);
        Assert.Contains(
            "<ProjectReference Include=\"src/Sample.Console.Contracts/Sample.Console.Contracts.csproj\" />",
            project);
        var settings = Text(
            outputs,
            "ProgramKitGenerated/Commands/ObserveRun/ObserveRunSettings.cs");
        Assert.Contains(
            "[global::Spectre.Console.Cli.CommandArgument(0, \"<target>\")]",
            settings);
        Assert.Contains(
            "public global::System.Int32? Value1",
            settings);
        var requestFactory = Text(
            outputs,
            "ProgramKitGenerated/Commands/ObserveRun/ObserveRunRequestFactory.cs");
        Assert.Contains(
            "settings.Value1 ?? 1",
            requestFactory);
        var commandSource = Text(
            outputs,
            "ProgramKitGenerated/Commands/ObserveRun/ObserveRunCommand.cs");
        Assert.Contains(
            "global::Orbyss.ProgramKit.ConsoleContractFixtures.Contracts.IMetadataFixtureHandler handler",
            commandSource);
        Assert.Contains(
            "return await handler.HandleAsync(request, cancellationToken)",
            commandSource);
        var program = Text(outputs, "ProgramKitGenerated/Program.cs");
        Assert.Contains(".AddBranch(\"observe\"", program);
        Assert.Contains(
            ".AddCommand<global::GeneratedHost.Commands.ObserveRunCommand>(\"execute\")",
            program);
        Assert.Contains(
            ".AddCommand<global::GeneratedHost.Commands.ObserveRunCommand>(\"run-observation\")",
            program);
        foreach (var output in outputs)
        {
            Assert.IsFalse(
                output.Content.Span.StartsWith(
                    new byte[] { 0xEF, 0xBB, 0xBF }));
            Assert.IsFalse(
                output.Content.Span.Contains((byte)'\r'));
        }

        var repeated = await sut.GenerateAsync(
            input,
            CancellationToken.None);
        Assert.AreSequenceEqual(
            outputs.Select(static output => output.RelativePath).ToArray(),
            repeated.Select(static output => output.RelativePath).ToArray());
        foreach (var output in outputs)
        {
            Assert.AreSequenceEqual(
                output.Content.ToArray(),
                repeated.Single(candidate =>
                    candidate.RelativePath == output.RelativePath).Content.ToArray());
        }
    }

    [TestMethod]
    public async Task GenerationRejectsDocumentFromAnotherShellRevision()
    {
        var shell = DotNetTestContractFactory.Shell();
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "reviewed",
            '6');
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Console);
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        document = document with
        {
            Provenance = document.Provenance with
            {
                ShellRevision = DotNetTestContractFactory.Ref(
                    "shell",
                    "other",
                    '8'),
            },
        };
        var coordinator = CreateCoordinator();
        ConsoleHostGenerator sut = new(coordinator);
        var revision = DocumentRevision(document);
        var input = new DotNetHostGenerationInput(
            shell,
            shellRevision,
            CreateLock(shell, shellRevision),
            host.Identity,
            null,
            document,
            null,
            revision,
            DotNetConsoleBindingTestFactory.GenerationInput(
                document,
                revision));

        var exception = await Assert.ThrowsExactlyAsync<DotNetKitException>(
            async () => await sut.GenerateAsync(
                input,
                CancellationToken.None));

        Assert.AreEqual(
            DotNetDiagnosticIds.InvalidIntegratorDocument,
            exception.DiagnosticId);
    }

    [TestMethod]
    [DataRow("missing")]
    [DataRow("stale-version")]
    [DataRow("mismatched-digest")]
    public async Task ConsoleGenerationRejectsInvalidDocumentRevision(
        string invalidRevisionKind)
    {
        var shell = DotNetTestContractFactory.Shell();
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "reviewed",
            '6');
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Console);
        var document = DotNetTestContractFactory.ConsoleDocument(shell);
        var exactRevision = DocumentRevision(document);
        var revision = invalidRevisionKind switch
        {
            "missing" => null,
            "stale-version" => exactRevision with
            {
                Version = new SemanticVersion("2.0.0"),
            },
            "mismatched-digest" => exactRevision with
            {
                Digest = DotNetTestContractFactory.Digest('f'),
            },
            _ => throw new AssertFailedException("Unsupported invalid revision kind."),
        };
        ConsoleHostGenerator sut = new(CreateCoordinator());
        var input = new DotNetHostGenerationInput(
            shell,
            shellRevision,
            CreateLock(shell, shellRevision),
            host.Identity,
            null,
            document,
            null,
            revision,
            DotNetConsoleBindingTestFactory.GenerationInput(
                document,
                exactRevision));

        var exception = await Assert.ThrowsExactlyAsync<DotNetKitException>(
            async () => await sut.GenerateAsync(
                input,
                CancellationToken.None));

        Assert.AreEqual(
            DotNetDiagnosticIds.InvalidOpenConsoleDocumentRevision,
            exception.DiagnosticId);
        Assert.AreEqual(
            "/documentation/openConsoleDocumentRevision",
            exception.Path);
    }

    [TestMethod]
    public async Task NonConsoleGenerationRejectsExtraOpenConsoleRevision()
    {
        var shell = DotNetTestContractFactory.Shell();
        var shellRevision = DotNetTestContractFactory.Ref(
            "shell",
            "reviewed",
            '6');
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Api);
        var apiDocument = DotNetTestContractFactory.ApiDocument(shell);
        ApiHostGenerator sut = new(CreateCoordinator());
        var input = new DotNetHostGenerationInput(
            shell,
            shellRevision,
            CreateLock(shell, shellRevision),
            host.Identity,
            apiDocument,
            null,
            null,
            DotNetTestContractFactory.Ref(
                "document",
                "console",
                'e'));

        var exception = await Assert.ThrowsExactlyAsync<DotNetKitException>(
            async () => await sut.GenerateAsync(
                input,
                CancellationToken.None));

        Assert.AreEqual(
            DotNetDiagnosticIds.InvalidOpenConsoleDocumentRevision,
            exception.DiagnosticId);
    }

    private static DotNetShellLockDocument CreateLock(
        DotNetShellDocument shell,
        ArtifactReference shellRevision)
    {
        var validator = new DotNetShellValidator(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());
        DotNetShellLockBuilder builder = new(validator);
        return builder.Build(shell, shellRevision);
    }

    private static string Text(
        ImmutableArray<Orbyss.ProgramKit.Workbench.Operations.Generation.GeneratedOutput> outputs,
        string relativePath) =>
        System.Text.Encoding.UTF8.GetString(
            outputs.Single(output =>
                output.RelativePath == relativePath).Content.Span);

    private static DotNetHostGenerationCoordinator CreateCoordinator()
    {
        var documentWriter = CreateDocumentWriter();
        return new DotNetHostGenerationCoordinator(
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator(),
                new TransportFailureProfileValidator(),
                new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
                DotNetTestContractFactory.ProviderCatalog()),
            new DotNetHostLockSelector(),
            new DotNetHostSourceRenderer(
                new DotNetConfigurationProjectionCompiler(
                    DotNetTestContractFactory.ProviderRegistry()),
                new DotNetTelemetryProjectionCompiler(),
                new DotNetTransportFailureProjectionCompiler(),
                new DotNetSecurityProjectionCompiler(),
                new Orbyss.ProgramKit.DotNet.Generation.FastEndpoints.DotNetFastEndpointsProjectionCompiler()),
            documentWriter,
            new DotNetIntegratorDocumentValidator(new OpenConsoleDocumentValidator()),
            Orbyss.ProgramKit.DotNet.Generation.Console.Composition.DotNetConsoleGenerationComposition.Create());
    }

    private static DotNetDocumentWriter CreateDocumentWriter()
    {
        var serializer = CreateSerializer();
        ProgramKitJsonCanonicalizer canonicalizer = new();
        OpenApiDocumentWriter openApiWriter = new(canonicalizer);
        return new DotNetDocumentWriter(
            openApiWriter,
            serializer);
    }

    private static ProgramKitJsonSerializer CreateSerializer()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder jsonBuilder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(jsonBuilder);
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitJsonSerializer serializer = new(
            jsonBuilder.Freeze(),
            canonicalizer);
        return serializer;
    }

    private static ArtifactReference DocumentRevision(
        OpenConsoleDocument document)
    {
        var content = CreateDocumentWriter().Write(document);
        return new ArtifactReference(
            DotNetTestContractFactory.Id("document", "console"),
            document.DocumentVersion,
            new Sha256Digest(
                string.Concat(
                    "sha256:",
                    Convert.ToHexStringLower(
                        SHA256.HashData(content.Span)))));
    }
}
