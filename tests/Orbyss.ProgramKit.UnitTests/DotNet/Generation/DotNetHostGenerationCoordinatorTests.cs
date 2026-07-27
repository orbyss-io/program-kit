using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
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
        var input = new DotNetHostGenerationInput(
            shell,
            shellRevision,
            lockDocument,
            host.Identity,
            null,
            document,
            null,
            DocumentRevision(document));

        var outputs = await sut.GenerateAsync(
            input,
            CancellationToken.None);

        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "GeneratedHost.csproj"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "ProgramKitGenerated/Commands/GeneratedConsoleParser.cs"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "docs/open-console.json"));
        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath == "shell.lock.json"));
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
        var input = new DotNetHostGenerationInput(
            shell,
            shellRevision,
            CreateLock(shell, shellRevision),
            host.Identity,
            null,
            document,
            null,
            DocumentRevision(document));

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
            revision);

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
            new DotNetIntegratorDocumentValidator());
    }

    private static DotNetDocumentWriter CreateDocumentWriter()
    {
        ProgramKitJsonRegistryFactory registryFactory = new();
        ProgramKitJsonBuilder jsonBuilder = new(registryFactory);
        DotNetJsonProfileRegistration registration = new();
        registration.Register(jsonBuilder);
        ProgramKitJsonCanonicalizer canonicalizer = new();
        ProgramKitJsonSerializer serializer = new(
            jsonBuilder.Freeze(),
            canonicalizer);
        OpenApiDocumentWriter openApiWriter = new(canonicalizer);
        DotNetDocumentWriter documentWriter = new(
            openApiWriter,
            serializer);
        return documentWriter;
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
