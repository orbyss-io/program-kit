using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Validation;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace ObservatoryScheduling.Tests.Configuration;

public sealed class GeneratedHostArtifactTests
{
    [Test]
    public async Task TypedShellLockDocumentsAndHostOutputsAreDeterministic()
    {
        var shell = ObservatoryDotNetContractFactory.CreateShell();
        var shellRevision = ObservatoryDotNetContractFactory.ShellRevision();
        DotNetConfigurationProviderComposition providerComposition =
            new DotNetConfigurationProviderComposition();
        var shellValidator = new DotNetShellValidator(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            providerComposition.CreateBuiltInCatalog());
        var lockBuilder = new DotNetShellLockBuilder(shellValidator);
        var shellLock = lockBuilder.Build(shell, shellRevision);
        var documentValidator = new DotNetIntegratorDocumentValidator();
        var api = ObservatoryDotNetContractFactory.CreateApiDocument(shell);
        var console =
            ObservatoryDotNetContractFactory.CreateConsoleDocument(shell);
        var worker =
            ObservatoryDotNetContractFactory.CreateWorkerDocument(shell);

        FixtureAssert.IsValid(shellValidator.Validate(shell));
        FixtureAssert.IsValid(documentValidator.Validate(api));
        FixtureAssert.IsValid(documentValidator.Validate(console));
        FixtureAssert.IsValid(documentValidator.Validate(worker));
        FixtureAssert.HasCount(3, shellLock.HostLocks);

        var coordinator = CreateCoordinator();
        foreach (var host in shell.Hosts)
        {
            var input = host.Kind switch
            {
                DotNetHostKind.Api => new DotNetHostGenerationInput(
                    shell,
                    shellRevision,
                    shellLock,
                    host.Identity,
                    api,
                    null,
                    null),
                DotNetHostKind.Console => new DotNetHostGenerationInput(
                    shell,
                    shellRevision,
                    shellLock,
                    host.Identity,
                    null,
                    console,
                    null),
                DotNetHostKind.Worker => new DotNetHostGenerationInput(
                    shell,
                    shellRevision,
                    shellLock,
                    host.Identity,
                    null,
                    null,
                    worker),
                _ => throw new InvalidOperationException(
                    $"Unsupported host kind {host.Kind}."),
            };

            var first = await coordinator.GenerateAsync(
                input,
                host.Kind,
                CancellationToken.None);
            var second = await coordinator.GenerateAsync(
                input,
                host.Kind,
                CancellationToken.None);

            FixtureAssert.AreEqual(first.Length, second.Length);
            for (var index = 0; index < first.Length; index++)
            {
                FixtureAssert.AreEqual(
                    first[index].RelativePath,
                    second[index].RelativePath);
                FixtureAssert.SequenceEqual(
                    first[index].Content.Span,
                    second[index].Content.Span);
            }
        }
    }

    private static DotNetHostGenerationCoordinator CreateCoordinator()
    {
        var registryFactory = new ProgramKitJsonRegistryFactory();
        var jsonBuilder = new ProgramKitJsonBuilder(registryFactory);
        var registration = new DotNetJsonProfileRegistration();
        registration.Register(jsonBuilder);
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var serializer = new ProgramKitJsonSerializer(
            jsonBuilder.Freeze(),
            canonicalizer);
        var openApiWriter = new OpenApiDocumentWriter(canonicalizer);
        var documentWriter = new DotNetDocumentWriter(
            openApiWriter,
            serializer);
        DotNetConfigurationProviderComposition providerComposition =
            new DotNetConfigurationProviderComposition();
        return new DotNetHostGenerationCoordinator(
            new DotNetShellValidator(
                new ArtifactReferenceValidator(),
                new OperationContractDescriptorValidator(),
                providerComposition.CreateBuiltInCatalog()),
            new DotNetHostLockSelector(),
            new DotNetHostSourceRenderer(
                new DotNetConfigurationProjectionCompiler(
                    providerComposition.CreateBuiltInRegistry()),
                new DotNetTelemetryProjectionCompiler()),
            documentWriter,
            new DotNetIntegratorDocumentValidator());
    }
}
