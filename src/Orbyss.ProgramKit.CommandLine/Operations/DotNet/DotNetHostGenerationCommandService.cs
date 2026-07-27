using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.DotNet.Composition;
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

/// <summary>Default exact-input host generation behavior shared by generate and publish.</summary>
public sealed class DotNetHostGenerationCommandService :
    IDotNetHostGenerationCommandService
{
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly IDotNetArtifactInputResolver inputResolver;
    private readonly IDotNetShellLockBuilder lockBuilder;
    private readonly IDotNetHostLockSelector lockSelector;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> apiGeneration;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> consoleGeneration;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> workerGeneration;

    /// <summary>Initializes all parsing, resolution, locking, and generation behavior.</summary>
    public DotNetHostGenerationCommandService(
        ICommandFileSystem fileSystem,
        IProgramKitJsonSerializer serializer,
        IDotNetArtifactInputResolver inputResolver,
        IDotNetShellLockBuilder lockBuilder,
        IDotNetHostLockSelector lockSelector,
        IWorkbenchGenerationService<DotNetHostGenerationInput> apiGeneration,
        IWorkbenchGenerationService<DotNetHostGenerationInput> consoleGeneration,
        IWorkbenchGenerationService<DotNetHostGenerationInput> workerGeneration)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
        this.inputResolver = inputResolver ??
            throw new ArgumentNullException(nameof(inputResolver));
        this.lockBuilder = lockBuilder ??
            throw new ArgumentNullException(nameof(lockBuilder));
        this.lockSelector = lockSelector ??
            throw new ArgumentNullException(nameof(lockSelector));
        this.apiGeneration = apiGeneration ??
            throw new ArgumentNullException(nameof(apiGeneration));
        this.consoleGeneration = consoleGeneration ??
            throw new ArgumentNullException(nameof(consoleGeneration));
        this.workerGeneration = workerGeneration ??
            throw new ArgumentNullException(nameof(workerGeneration));
    }

    /// <inheritdoc />
    public async ValueTask<DotNetHostGenerationCommandResult> GenerateAsync(
        DotNetHostGenerationCommandRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        var profile = DotNetJsonProfiles.ShellBootstrap.Reference;
        var limits = JsonSerializationLimits.Default;
        var manifestPath = Path.GetFullPath(request.ArtifactManifestPath);
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
            request.ShellPath,
            cancellationToken).ConfigureAwait(false);
        var shell = serializer.Read<DotNetShellDocument>(
            shellBytes,
            profile,
            limits);
        var hostIdentity = new ProgramKitIdentifier(request.HostIdentity);
        var host = ResolveHost(shell, hostIdentity, request.ExpectedKind);
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
            host.Kind,
            projection.Content,
            profile,
            limits);
        var shellRevision = documentInput.Provenance.ShellRevision;
        EnsureShellDigest(shellBytes.Span, shellRevision.Digest);
        var shellLock = lockBuilder.Build(shell, shellRevision);
        var hostLock = lockSelector.Resolve(shellLock, hostIdentity, host.Kind);
        var generationInput = new DotNetHostGenerationInput(
            shell,
            shellRevision,
            shellLock,
            hostIdentity,
            documentInput.OpenApi,
            documentInput.OpenConsole,
            documentInput.OpenWorker,
            host.Kind == DotNetHostKind.Console
                ? projectionRevision
                : null);
        var service = SelectService(host.Kind);
        var result = await service.GenerateAsync(
            new GenerationRequest<DotNetHostGenerationInput>(
                generationInput,
                Path.GetFullPath(request.OutputRoot),
                GenerationCollisionPolicy.Fail,
                GenerationLimits.Default),
            cancellationToken).ConfigureAwait(false);
        if (!result.Validation.IsValid)
        {
            var diagnostic = result.Validation.Diagnostics[0];
            throw new InvalidDataException(
                string.Concat(
                    diagnostic.Id,
                    " ",
                    diagnostic.Message,
                    " at ",
                    diagnostic.Path));
        }

        return new DotNetHostGenerationCommandResult(
            shell,
            shellRevision,
            shellLock,
            host,
            hostLock);
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

    private static DotNetHostDefinition ResolveHost(
        DotNetShellDocument shell,
        ProgramKitIdentifier identity,
        DotNetHostKind? expectedKind)
    {
        var matches = shell.Hosts
            .Where(candidate =>
                candidate.Identity == identity &&
                (expectedKind is null || candidate.Kind == expectedKind))
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

    private static DotNetDocumentInput FromApi(
        OpenApiDocumentProjection document) =>
        new(document.Provenance, document, null, null);

    private static DotNetDocumentInput FromConsole(
        OpenConsoleDocument document) =>
        new(document.Provenance, null, document, null);

    private static DotNetDocumentInput FromWorker(
        OpenWorkerDocument document) =>
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
}
