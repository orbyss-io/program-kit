using System.Collections.Immutable;
using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.DotNet.Documentation.Console;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

/// <summary>Explicit manifest-bound transport for API, Console, and Worker generation.</summary>
public sealed class DotNetGenerateHostCommandOperation : ICommandOperation
{
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly IDotNetArtifactInputResolver inputResolver;
    private readonly IDotNetShellLockBuilder lockBuilder;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> apiGeneration;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> consoleGeneration;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> workerGeneration;

    /// <summary>Initializes the adapter with all parsing, resolution, lock, and generation behavior.</summary>
    public DotNetGenerateHostCommandOperation(
        ICommandFileSystem fileSystem,
        IProgramKitJsonSerializer serializer,
        IDotNetArtifactInputResolver inputResolver,
        IDotNetShellLockBuilder lockBuilder,
        IWorkbenchGenerationService<DotNetHostGenerationInput> apiGeneration,
        IWorkbenchGenerationService<DotNetHostGenerationInput> consoleGeneration,
        IWorkbenchGenerationService<DotNetHostGenerationInput> workerGeneration)
    {
        this.fileSystem = fileSystem ?? throw new ArgumentNullException(nameof(fileSystem));
        this.serializer = serializer ?? throw new ArgumentNullException(nameof(serializer));
        this.inputResolver = inputResolver ??
            throw new ArgumentNullException(nameof(inputResolver));
        this.lockBuilder = lockBuilder ?? throw new ArgumentNullException(nameof(lockBuilder));
        this.apiGeneration = apiGeneration ??
            throw new ArgumentNullException(nameof(apiGeneration));
        this.consoleGeneration = consoleGeneration ??
            throw new ArgumentNullException(nameof(consoleGeneration));
        this.workerGeneration = workerGeneration ??
            throw new ArgumentNullException(nameof(workerGeneration));
    }

    /// <inheritdoc />
    public string CommandKey => "dotnet.generate-host";

    /// <inheritdoc />
    public async ValueTask<CommandOperationResult> ExecuteAsync(
        CommandInvocation invocation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(invocation);
        try
        {
            var profile = DotNetJsonProfiles.ShellBootstrap.Reference;
            var limits = JsonSerializationLimits.Default;
            var manifestPath = Path.GetFullPath(
                invocation.RequiredOption("artifact-manifest"));
            var readRoot = Path.GetDirectoryName(manifestPath) ??
                throw new InvalidDataException(
                    "The explicit artifact manifest has no read root.");
            var manifestBytes = await fileSystem.ReadAllBytesAsync(
                manifestPath,
                cancellationToken).ConfigureAwait(false);
            var manifest = serializer.Read<DotNetArtifactInputManifest>(
                manifestBytes,
                profile,
                limits);
            var shellBytes = await fileSystem.ReadAllBytesAsync(
                invocation.RequiredOption("shell"),
                cancellationToken).ConfigureAwait(false);
            var shell = serializer.Read<DotNetShellDocument>(
                shellBytes,
                profile,
                limits);
            var kind = ParseKind(invocation.Arguments[0]);
            var hostIdentity = new ProgramKitIdentifier(
                invocation.RequiredOption("host"));
            var host = ResolveHost(shell, hostIdentity, kind);
            await VerifyInputAsync(
                readRoot,
                manifest,
                shell.InputVersionMapRevision,
                cancellationToken).ConfigureAwait(false);
            await VerifyInputAsync(
                readRoot,
                manifest,
                shell.InputVersionSelectionRevision,
                cancellationToken).ConfigureAwait(false);
            var projectionRevision = ResolveDocumentRevision(
                manifest,
                hostIdentity);
            var projection = await inputResolver.ResolveAsync(
                readRoot,
                manifest,
                projectionRevision,
                cancellationToken).ConfigureAwait(false);
            var documentInput = ReadDocument(
                kind,
                projection.Content,
                profile,
                limits);
            var shellRevision = documentInput.Provenance.ShellRevision;
            EnsureShellDigest(shellBytes.Span, shellRevision.Digest);
            var shellLock = lockBuilder.Build(shell, shellRevision);
            var generationInput = new DotNetHostGenerationInput(
                shell,
                shellRevision,
                shellLock,
                hostIdentity,
                documentInput.OpenApi,
                documentInput.OpenConsole,
                documentInput.OpenWorker);
            var service = SelectService(kind);
            var result = await service.GenerateAsync(
                new GenerationRequest<DotNetHostGenerationInput>(
                    generationInput,
                    Path.GetFullPath(invocation.RequiredOption("output")),
                    GenerationCollisionPolicy.Fail,
                    GenerationLimits.Default),
                cancellationToken).ConfigureAwait(false);
            return result.Validation.IsValid
                ? CommandOperationResult.Success()
                : Failure(result.Validation.Diagnostics);
        }
        catch (DotNetKitException exception)
        {
            return new CommandOperationResult(
                CommandExitCode.ConformanceFailure,
                default,
                [
                    new CommandDiagnostic(
                        exception.DiagnosticId,
                        "error",
                        exception.Message,
                        exception.Path),
                ]);
        }
    }

    private async ValueTask VerifyInputAsync(
        string readRoot,
        DotNetArtifactInputManifest manifest,
        ArtifactReference revision,
        CancellationToken cancellationToken)
    {
        _ = await inputResolver.ResolveAsync(
            readRoot,
            manifest,
            revision,
            cancellationToken).ConfigureAwait(false);
    }

    private IWorkbenchGenerationService<DotNetHostGenerationInput> SelectService(
        DotNetHostKind kind) =>
        kind switch
        {
            DotNetHostKind.Api => apiGeneration,
            DotNetHostKind.Console => consoleGeneration,
            DotNetHostKind.Worker => workerGeneration,
            _ => throw new ArgumentOutOfRangeException(nameof(kind)),
        };

    private static DotNetHostKind ParseKind(string value) =>
        value switch
        {
            "api" => DotNetHostKind.Api,
            "console" => DotNetHostKind.Console,
            "worker" => DotNetHostKind.Worker,
            _ => throw new InvalidDataException("The host kind is unsupported."),
        };

    private static DotNetHostDefinition ResolveHost(
        DotNetShellDocument shell,
        ProgramKitIdentifier identity,
        DotNetHostKind kind)
    {
        var matches = shell.Hosts
            .Where(candidate => candidate.Identity == identity && candidate.Kind == kind)
            .ToArray();
        return matches.Length == 1
            ? matches[0]
            : throw new InvalidDataException(
                "The requested host must resolve exactly once with the requested kind.");
    }

    private static ArtifactReference ResolveDocumentRevision(
        DotNetArtifactInputManifest manifest,
        ProgramKitIdentifier hostIdentity)
    {
        var revisions = manifest.HostDocuments.IsDefault
            ? []
            : manifest.HostDocuments
            .Where(binding => binding.HostIdentity == hostIdentity)
            .Select(static binding => binding.DocumentRevision)
            .ToArray();
        return revisions.Length == 1
            ? revisions[0]
            : throw new InvalidDataException(
                "The artifact manifest must bind the selected host to one exact integrator-document input.");
    }

    private DotNetDocumentInput ReadDocument(
        DotNetHostKind kind,
        ReadOnlyMemory<byte> content,
        JsonSerializationProfileRef profile,
        JsonSerializationLimits limits) =>
        kind switch
        {
            DotNetHostKind.Api => FromApi(
                serializer.Read<OpenApiDocumentProjection>(
                    content,
                    profile,
                    limits)),
            DotNetHostKind.Console => FromConsole(
                serializer.Read<OpenConsoleDocument>(
                    content,
                    profile,
                    limits)),
            DotNetHostKind.Worker => FromWorker(
                serializer.Read<OpenWorkerDocument>(
                    content,
                    profile,
                    limits)),
            _ => throw new ArgumentOutOfRangeException(nameof(kind)),
        };

    private static DotNetDocumentInput FromApi(OpenApiDocumentProjection document) =>
        new(document.Provenance, document, null, null);

    private static DotNetDocumentInput FromConsole(OpenConsoleDocument document) =>
        new(document.Provenance, null, document, null);

    private static DotNetDocumentInput FromWorker(OpenWorkerDocument document) =>
        new(document.Provenance, null, null, document);

    private static void EnsureShellDigest(
        ReadOnlySpan<byte> shellBytes,
        Sha256Digest expected)
    {
        var actual = string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(shellBytes)));
        if (!string.Equals(actual, expected.Value, StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                "The explicit shell bytes do not match the projection's exact shell revision.");
        }
    }

    private static CommandOperationResult Failure(
        ImmutableArray<ProgramKitDiagnostic> diagnostics) =>
        new(
            CommandExitCode.ConformanceFailure,
            default,
            diagnostics.Select(diagnostic =>
                    new CommandDiagnostic(
                        diagnostic.Id,
                        diagnostic.Severity.ToString().ToLowerInvariant(),
                        diagnostic.Message,
                        diagnostic.Path))
                .ToImmutableArray());

}
