using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.Architecture.Schemas;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Hosting.IO;
using Orbyss.ProgramKit.CommandLine.Operations;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Catalog;
using Orbyss.ProgramKit.CommandLine.Operations.Execution;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Json;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;
using Orbyss.ProgramKit.CommandLine.Operations.Publishing;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.CommandLine.Operations.Validation;
using Orbyss.ProgramKit.Development.Schemas;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Planning.Schemas;
using Orbyss.ProgramKit.Operations.Contracts.Schemas;
using Orbyss.ProgramKit.Operations.Contracts.Validation;
using Orbyss.ProgramKit.Quality.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Composition;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.Tasks.Core.Schemas;
using Orbyss.ProgramKit.Tasks.Schedules.Schemas;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;
using Orbyss.ProgramKit.Workbench.Composition.Generation;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.CommandLine.Composition;

/// <summary>Explicit baseline composition for the standalone .NET tool.</summary>
public static class CommandLineComposition
{
    /// <summary>Creates the standalone system-console composition.</summary>
    public static ICommandApplication CreateDefault()
    {
        ICommandConsole console = new SystemCommandConsole();
        return CreateDefault(console);
    }

    /// <summary>Creates the W050 command transport without ambient discovery.</summary>
    public static ICommandApplication CreateDefault(ICommandConsole console)
    {
        ArgumentNullException.ThrowIfNull(console);
        var registryFactory = new ProgramKitJsonRegistryFactory();
        var jsonBuilder = new ProgramKitJsonBuilder(registryFactory);
        jsonBuilder.AddOwnedProfile(
            CommandLineJsonProfiles.Diagnostics,
            new JsonProfileOwnedMechanics(
                CommandLineJsonProfiles.Diagnostics.Reference,
                new ProgramKitIdentifier("pkid:package:program-kit:command-line"),
                CommandDiagnosticJsonContext.Default));
        DotNetJsonProfileRegistration dotNetJson = new();
        dotNetJson.Register(jsonBuilder);
        LocalOperationsJsonProfileRegistration localOperationsJson = new();
        localOperationsJson.Register(jsonBuilder);
        var canonicalizer = new ProgramKitJsonCanonicalizer();
        var serializer = new ProgramKitJsonSerializer(
            jsonBuilder.Freeze(),
            canonicalizer);
        ICommandParser parser = new CommandParser(CommandDescriptorCatalog.All);
        var operationChain = CreateBaselineOperations(canonicalizer, serializer);
        ICommandOperationRegistry operations =
            new CommandOperationRegistry(operationChain);
        ICommandDiagnosticFormatter formatter =
            new CommandDiagnosticFormatter(serializer);
        return new CommandApplication(parser, operations, console, formatter);
    }

    private static ICommandOperationChain CreateBaselineOperations(
        IProgramKitJsonCanonicalizer canonicalizer,
        IProgramKitJsonSerializer serializer)
    {
        ICommandFileSystem fileSystem = new CommandFileSystem();
        CommandProcessRunner processRunner = new();
        ICommandSchemaSelector schemaSelector = new CommandSchemaSelector(
            new ArtifactsSchemaModule(),
            new ArchitectureSchemaModule(),
            new QualitySchemaModule(),
            new PlanningSchemaModule(),
            new DevelopmentSchemaModule(),
            new SerializationJsonSchemaModule(),
            new TasksCoreSchemaModule(),
            new TaskSchedulesSchemaModule(),
            new DotNetSchemaModule(
                new OperationsSchemaModule(),
                new Orbyss.ProgramKit.SecretResolution.Contracts.Schemas.SecretResolutionSchemaModule()));
        var moduleValidator = new ProgramKitSchemaModuleValidator();
        IWorkbenchSchemaValidator schemaValidator =
            new JsonSchemaWorkbenchValidator(canonicalizer, moduleValidator);
        DotNetConfigurationProviderComposition providerComposition =
            new DotNetConfigurationProviderComposition();
        var providerCatalog = providerComposition.CreateBuiltInCatalog();
        var shellValidator = new DotNetShellValidator(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            providerCatalog);
        IDotNetShellLockBuilder lockBuilder =
            new DotNetShellLockBuilder(shellValidator);
        DotNetHostLockSelector hostLockSelector = new();
        var coordinator = new DotNetHostGenerationCoordinator(
            shellValidator,
            hostLockSelector,
            new DotNetHostSourceRenderer(
                new DotNetConfigurationProjectionCompiler(
                    providerComposition.CreateBuiltInRegistry()),
                new DotNetTelemetryProjectionCompiler(),
                new DotNetTransportFailureProjectionCompiler(),
                new DotNetSecurityProjectionCompiler(),
                new Orbyss.ProgramKit.DotNet.Generation.FastEndpoints.DotNetFastEndpointsProjectionCompiler()),
            new DotNetDocumentWriter(
                new OpenApiDocumentWriter(canonicalizer),
                serializer),
            new DotNetIntegratorDocumentValidator());
        IWorkbenchOutputWorkspace outputWorkspace =
            new FileSystemWorkbenchOutputWorkspace();
        IWorkbenchGenerationService<DotNetHostGenerationInput> apiGeneration =
            new WorkbenchGenerationService<DotNetHostGenerationInput>(
                new ApiHostGenerator(coordinator),
                outputWorkspace);
        IWorkbenchGenerationService<DotNetHostGenerationInput> consoleGeneration =
            new WorkbenchGenerationService<DotNetHostGenerationInput>(
                new ConsoleHostGenerator(coordinator),
                outputWorkspace);
        IWorkbenchGenerationService<DotNetHostGenerationInput> workerGeneration =
            new WorkbenchGenerationService<DotNetHostGenerationInput>(
                new WorkerHostGenerator(coordinator),
                outputWorkspace);
        DotNetHostGenerationCommandService hostGeneration = new(
            fileSystem,
            serializer,
            new FileSystemDotNetArtifactInputResolver(),
            lockBuilder,
            hostLockSelector,
            apiGeneration,
            consoleGeneration,
            workerGeneration);
        ICommandOperation dotNetGeneration =
            new DotNetGenerateHostCommandOperation(hostGeneration);
        IKiotaForeignClientGenerator kiotaGenerator =
            new KiotaForeignClientGenerator(
                fileSystem,
                processRunner,
                new KiotaToolPackageMaterializer(fileSystem));
        ICommandOperation kiotaGeneration =
            new KiotaGenerateClientCommandOperation(kiotaGenerator);
        IArtifactEnvelopeValidator artifactEnvelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        LocalPackagePreparationService packagePreparation = new(
            fileSystem,
            processRunner,
            new PackageArchiveInspector(),
            serializer,
            new VersionMapDocumentValidator(artifactEnvelopeValidator),
            new VersionSelectionDocumentValidator(artifactEnvelopeValidator));
        ICommandOperation packagePreparationOperation =
            new PrepareLocalPackagesCommandOperation(packagePreparation);
        LocalApplicationPublisher localPublisher = new(
            fileSystem,
            processRunner,
            hostGeneration,
            new LocalPackageRootVerifier(fileSystem, serializer),
            new NuGetSourceConfigurationWriter(),
            new NuGetLockVerifier(serializer),
            serializer);
        ICommandOperation localPublishOperation =
            new PublishLocalApplicationCommandOperation(localPublisher);
        ICommandOperation capabilityCatalogOperation =
            new RenderCapabilityCatalogCommandOperation(
                new CapabilityCatalogRenderer(
                    fileSystem,
                    new CapabilityIndexParser()));
        ICommandOperation capabilityBundleOperation =
            new VerifyCapabilityBundleCommandOperation(
                new CapabilityBundleVerifier(
                    new CapabilityBundleManifestReader()));
        ICommandOperationChain? chain = null;
        foreach (var descriptor in CommandDescriptorCatalog.All.Reverse())
        {
            ICommandOperation operation = descriptor.Key switch
            {
                "validate" => new ValidateCommandOperation(
                    fileSystem,
                    schemaSelector,
                    schemaValidator),
                "normalize" => new NormalizeCommandOperation(
                    fileSystem,
                    canonicalizer),
                "digest" => new DigestCommandOperation(
                    fileSystem,
                    canonicalizer),
                "dotnet.generate-host" => dotNetGeneration,
                "dotnet.generate-client" => kiotaGeneration,
                "packages.prepare-local" => packagePreparationOperation,
                "dotnet.publish-local" => localPublishOperation,
                "capabilities.render-catalog" => capabilityCatalogOperation,
                "capabilities.verify-bundle" => capabilityBundleOperation,
                _ => new UnavailableCommandOperation(
                    descriptor.Key,
                    BackingWorkUnit(descriptor.Key)),
            };
            chain = new CommandOperationChain(operation, chain);
        }

        return chain ?? throw new InvalidOperationException(
            "The frozen command catalog cannot be empty.");
    }

    private static string BackingWorkUnit(string commandKey) =>
        commandKey.StartsWith("capabilities.", StringComparison.Ordinal)
            ? "PK-W070"
            : commandKey is "packages.prepare-local" or "dotnet.publish-local"
                ? "PK-W065"
                : "an explicit Workbench operation adapter";
}
