using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
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
            null);

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
            null);

        var exception = await Assert.ThrowsExactlyAsync<DotNetKitException>(
            async () => await sut.GenerateAsync(
                input,
                CancellationToken.None));

        Assert.AreEqual(
            DotNetDiagnosticIds.InvalidIntegratorDocument,
            exception.DiagnosticId);
    }

    private static DotNetShellLockDocument CreateLock(
        DotNetShellDocument shell,
        ArtifactReference shellRevision)
    {
        var validator = new DotNetShellValidator(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator());
        DotNetShellLockBuilder builder = new(validator);
        return builder.Build(shell, shellRevision);
    }

    private static DotNetHostGenerationCoordinator CreateCoordinator()
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
        return new DotNetHostGenerationCoordinator(
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator()),
            new DotNetHostLockSelector(),
            new DotNetHostSourceRenderer(),
            documentWriter,
            new DotNetIntegratorDocumentValidator());
    }
}
