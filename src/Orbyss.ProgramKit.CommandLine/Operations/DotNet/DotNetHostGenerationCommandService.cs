using System.Collections.Immutable;
using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Contracts.Product;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Validation;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Documentation;
using Orbyss.ProgramKit.DotNet.Documentation.Api;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.DotNet.Documentation.Worker;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;
using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet;

/// <summary>Default exact-input host generation behavior shared by generate and publish.</summary>
public sealed class DotNetHostGenerationCommandService :
    IDotNetHostGenerationCommandService
{
    private const string ConsoleManifestSchema =
        "pkid:schema:program-kit:dotnet-artifact-input-manifest@0.1.0-alpha.1";
    private const string ConsoleMaterializationLockFile =
        ".program-kit-console-inputs.lock.json";
    private const string ConsoleMaterializationLockSchema =
        "pkid:schema:program-kit:dotnet-console-input-materialization-lock@0.1.0-alpha.1";
    private static readonly SemanticVersion ConsoleManifestVersion =
        new("0.1.0-alpha.1");
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly IDotNetArtifactInputResolver inputResolver;
    private readonly IDotNetShellLockBuilder lockBuilder;
    private readonly IDotNetHostLockSelector lockSelector;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> apiGeneration;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> consoleGeneration;
    private readonly IWorkbenchGenerationService<DotNetHostGenerationInput> workerGeneration;
    private readonly IGeneratedOutputSealer outputSealer;

    /// <summary>Initializes all parsing, resolution, locking, and generation behavior.</summary>
    public DotNetHostGenerationCommandService(
        ICommandFileSystem fileSystem,
        IProgramKitJsonSerializer serializer,
        IDotNetArtifactInputResolver inputResolver,
        IDotNetShellLockBuilder lockBuilder,
        IDotNetHostLockSelector lockSelector,
        IWorkbenchGenerationService<DotNetHostGenerationInput> apiGeneration,
        IWorkbenchGenerationService<DotNetHostGenerationInput> consoleGeneration,
        IWorkbenchGenerationService<DotNetHostGenerationInput> workerGeneration,
        IGeneratedOutputSealer outputSealer)
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
        this.outputSealer = outputSealer ??
            throw new ArgumentNullException(nameof(outputSealer));
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
        var manifestSchema = SchemaIdentityReader.Read(manifestBytes.Span);
        DotNetArtifactInputManifest manifest;
        ImmutableArray<DotNetConsoleGenerationInputBinding>
            consoleGenerations;
        if (string.Equals(
                manifestSchema,
                ConsoleManifestSchema,
                StringComparison.Ordinal))
        {
            var alphaManifest =
                serializer.Read<DotNetArtifactInputManifestAlpha1>(
                    manifestBytes,
                    profile,
                    limits);
            manifest = alphaManifest.ToArtifactInputManifest();
            consoleGenerations = alphaManifest.ConsoleGenerations;
        }
        else
        {
            manifest = serializer.Read<DotNetArtifactInputManifest>(
                manifestBytes,
                profile,
                limits);
            consoleGenerations = default;
        }
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
        var shellRevision = documentInput.ShellRevision;
        EnsureShellDigest(shellBytes.Span, shellRevision.Digest);
        var shellLock = lockBuilder.Build(shell, shellRevision);
        var hostLock = lockSelector.Resolve(shellLock, hostIdentity, host.Kind);
        var outputRoot = Path.GetFullPath(request.OutputRoot);
        var consoleInput = await ResolveConsoleGenerationAsync(
            readRoot,
            outputRoot,
            manifestBytes,
            manifest,
            consoleGenerations,
            host,
            projectionRevision,
            documentInput.OpenConsole,
            profile,
            limits,
            cancellationToken).ConfigureAwait(false);
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
                : null,
            consoleInput);
        var service = SelectService(host.Kind);
        var anchorPath = GeneratedOutputPathPolicy.AnchorPath(outputRoot);
        if (fileSystem.FileExists(anchorPath) ||
            fileSystem.DirectoryExists(anchorPath))
        {
            throw new InvalidDataException(
                "The generated-output external anchor path already exists.");
        }

        var result = await service.GenerateAsync(
            new GenerationRequest<DotNetHostGenerationInput>(
                generationInput,
                outputRoot,
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

        var integrityManifestPath = GeneratedOutputPathPolicy.ResolveUnderRoot(
            outputRoot,
            GeneratedOutputIntegrityConstants.ManifestRelativePath,
            allowManifest: true);
        var integrityManifestBytes = await fileSystem.ReadAllBytesAsync(
            integrityManifestPath,
            cancellationToken).ConfigureAwait(false);
        await fileSystem.WriteAllBytesAsync(
            anchorPath,
            outputSealer.CreateAnchorBytes(integrityManifestBytes),
            cancellationToken).ConfigureAwait(false);
        return new DotNetHostGenerationCommandResult(
            shell,
            shellRevision,
            shellLock,
            host,
            hostLock);
    }

    private async ValueTask<DotNetConsoleGenerationInput?>
        ResolveConsoleGenerationAsync(
            string readRoot,
            string outputRoot,
            ReadOnlyMemory<byte> manifestBytes,
            DotNetArtifactInputManifest manifest,
            ImmutableArray<DotNetConsoleGenerationInputBinding>
                consoleGenerations,
            DotNetHostDefinition host,
            ArtifactReference documentRevision,
            OpenConsoleDocument? document,
            JsonSerializationProfileRef profile,
            JsonSerializationLimits limits,
            CancellationToken cancellationToken)
    {
        if (host.Kind != DotNetHostKind.Console)
        {
            return null;
        }

        if (!string.Equals(
                manifest.Schema,
                ConsoleManifestSchema,
                StringComparison.Ordinal) ||
            manifest.Version != ConsoleManifestVersion)
        {
            throw InvalidConsoleInput(
                "Console generation requires the exact alpha artifact-input manifest contract.");
        }

        var matches = consoleGenerations.IsDefault
            ? []
            : consoleGenerations
                .Where(candidate =>
                    candidate is not null &&
                    candidate.HostIdentity == host.Identity)
                .ToArray();
        if (matches.Length != 1)
        {
            throw InvalidConsoleInput(
                "The artifact manifest must bind the selected Console host to exactly one Console generation input.");
        }

        var selected = matches[0];
        if (selected.BindingRevision is null ||
            selected.ConsumerReferenceAssemblyRevision is null ||
            selected.CompilationReferenceRevisions.IsDefaultOrEmpty)
        {
            throw InvalidConsoleInput(
                "Console generation revisions must be initialized and non-empty.");
        }

        var referenceKeys = selected.CompilationReferenceRevisions
            .Select(ExactReferenceKey)
            .ToArray();
        if (referenceKeys.Distinct(StringComparer.Ordinal).Count() !=
                referenceKeys.Length ||
            !referenceKeys.SequenceEqual(
                referenceKeys.Order(StringComparer.Ordinal),
                StringComparer.Ordinal))
        {
            throw InvalidConsoleInput(
                "Console compilation reference revisions must be unique and ordinally ordered.");
        }

        var consumerKey = ExactReferenceKey(
            selected.ConsumerReferenceAssemblyRevision);
        if (referenceKeys.Count(key =>
                string.Equals(
                    key,
                    consumerKey,
                    StringComparison.Ordinal)) != 1)
        {
            throw InvalidConsoleInput(
                "The exact consumer reference assembly must occur once in the Console compilation reference set.");
        }

        var bindingInput = await inputResolver.ResolveAsync(
            readRoot,
            manifest,
            selected.BindingRevision,
            cancellationToken).ConfigureAwait(false);
        var binding = serializer.Read<DotNetConsoleBindingDocument>(
            bindingInput.Content,
            profile,
            limits);
        if (document is null ||
            binding.OpenConsoleDocumentRevision != documentRevision)
        {
            throw InvalidConsoleInput(
                "The Console binding must select the exact host document revision.");
        }

        var consumerInput = await inputResolver.ResolveAsync(
            readRoot,
            manifest,
            selected.ConsumerReferenceAssemblyRevision,
            cancellationToken).ConfigureAwait(false);
        if (!string.Equals(
                binding.ConsumerProject.RelativeReferenceAssemblyPath,
                consumerInput.RelativePath,
                StringComparison.Ordinal) ||
            binding.ConsumerProject.ReferenceAssemblyDigest !=
                consumerInput.Revision.Digest)
        {
            throw InvalidConsoleInput(
                "The Console binding consumer path and digest must match the exact manifest input.");
        }

        var pathComparer = OperatingSystem.IsWindows()
            ? StringComparer.OrdinalIgnoreCase
            : StringComparer.Ordinal;
        HashSet<string> resolvedPaths = new(pathComparer);
        var references =
            ImmutableArray.CreateBuilder<DotNetConsoleCompilationReference>();
        foreach (var revision in selected.CompilationReferenceRevisions)
        {
            var resolved = await inputResolver.ResolveAsync(
                readRoot,
                manifest,
                revision,
                cancellationToken).ConfigureAwait(false);
            if (!resolvedPaths.Add(resolved.FullPath))
            {
                throw InvalidConsoleInput(
                    "Console compilation reference paths must resolve uniquely.");
            }

            references.Add(
                new DotNetConsoleCompilationReference(
                    resolved.FullPath,
                    resolved.Revision.Digest));
        }

        var projectReferencePath =
            await ResolveMaterializedProjectReferenceAsync(
                readRoot,
                outputRoot,
                manifestBytes,
                binding,
                cancellationToken).ConfigureAwait(false);
        return new DotNetConsoleGenerationInput(
            binding,
            consumerInput.FullPath,
            references
                .OrderBy(static reference => reference.Path, StringComparer.Ordinal)
                .ToImmutableArray(),
            projectReferencePath);
    }

    private async ValueTask<string?> ResolveMaterializedProjectReferenceAsync(
        string readRoot,
        string outputRoot,
        ReadOnlyMemory<byte> manifestBytes,
        DotNetConsoleBindingDocument binding,
        CancellationToken cancellationToken)
    {
        var lockPath = Path.Combine(
            readRoot,
            ConsoleMaterializationLockFile);
        if (!fileSystem.FileExists(lockPath))
        {
            return null;
        }

        var lockBytes = await fileSystem.ReadAllBytesAsync(
            lockPath,
            cancellationToken).ConfigureAwait(false);
        var materializationLock =
            serializer.Read<DotNetConsoleInputMaterializationLock>(
                lockBytes,
                DotNetJsonProfiles.ShellBootstrap.Reference,
                JsonSerializationLimits.Default);
        var manifestDigest = Digest(manifestBytes.Span);
        if (!string.Equals(
                materializationLock.Schema,
                ConsoleMaterializationLockSchema,
                StringComparison.Ordinal) ||
            materializationLock.Version != ConsoleManifestVersion ||
            materializationLock.ProgramKitVersion.Value !=
                ProgramKitProductInfo.Version ||
            materializationLock.ManifestDigest != manifestDigest ||
            materializationLock.ConsumerProjectPath !=
                binding.ConsumerProject.RelativeProjectPath ||
            materializationLock.ConsumerReference.Revision.Digest !=
                binding.ConsumerProject.ReferenceAssemblyDigest ||
            materializationLock.ConsumerReference.RelativePath !=
                binding.ConsumerProject.RelativeReferenceAssemblyPath ||
            !materializationLock.ConsumerReference.Consumer)
        {
            throw InvalidConsoleInput(
                "The Console materialization lock is stale, incompatible, or inconsistent with the selected binding.");
        }

        var outputs = materializationLock.Outputs;
        if (outputs.IsDefaultOrEmpty ||
            outputs.Count(output =>
                output.RelativePath == "artifact-manifest.json" &&
                output.Digest == manifestDigest) != 1)
        {
            throw InvalidConsoleInput(
                "The Console materialization lock does not bind the selected artifact manifest.");
        }

        var expectedPaths = outputs
            .Select(static output => output.RelativePath)
            .Append(ConsoleMaterializationLockFile)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var actualPaths = fileSystem.EnumerateFiles(readRoot)
            .Select(path => LocalOperationPaths.RelativeTo(readRoot, path))
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!expectedPaths.SequenceEqual(
                actualPaths,
                StringComparer.Ordinal))
        {
            throw InvalidConsoleInput(
                "The Console materialization directory contains missing or unexpected files.");
        }

        foreach (var output in outputs)
        {
            var bytes = await fileSystem.ReadAllBytesAsync(
                LocalOperationPaths.ResolveBelow(
                    readRoot,
                    output.RelativePath,
                    "A Console materialization output"),
                cancellationToken).ConfigureAwait(false);
            if (Digest(bytes.Span) != output.Digest)
            {
                throw InvalidConsoleInput(
                    "A Console materialization output differs from its ownership lock.");
            }
        }

        var relativeWorkspacePath =
            materializationLock.WorkspaceRootRelativePath.Replace(
                '/',
                Path.DirectorySeparatorChar);
        var workspaceRoot = Path.GetFullPath(
            relativeWorkspacePath,
            readRoot);
        LocalOperationPaths.EnsureSafeRoot(workspaceRoot);
        _ = LocalOperationPaths.RelativeTo(workspaceRoot, readRoot);
        _ = LocalOperationPaths.RelativeTo(workspaceRoot, outputRoot);
        var projectPath = LocalOperationPaths.ResolveBelow(
            workspaceRoot,
            materializationLock.ConsumerProjectPath,
            "The materialized Console integration project");
        if (!fileSystem.FileExists(projectPath))
        {
            throw InvalidConsoleInput(
                "The materialized Console integration project no longer exists.");
        }

        var relativeProjectPath = Path.GetRelativePath(
                outputRoot,
                projectPath)
            .Replace(Path.DirectorySeparatorChar, '/');
        if (Path.IsPathRooted(relativeProjectPath))
        {
            throw InvalidConsoleInput(
                "The generated Console host and integration project must share one consumer workspace root.");
        }

        return relativeProjectPath;
    }

    private static Sha256Digest Digest(ReadOnlySpan<byte> content) =>
        new(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(content))));

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

    private static string ExactReferenceKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

    private static InvalidDataException InvalidConsoleInput(string message) =>
        new(
            string.Concat(
                DotNetDiagnosticIds.InvalidConsoleBinding,
                " /consoleGenerations: ",
                message));

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
        new(document.Provenance.ShellRevision, document, null, null);

    private static DotNetDocumentInput FromConsole(
        OpenConsoleDocument document) =>
        new(document.Provenance.ShellRevision, null, document, null);

    private static DotNetDocumentInput FromWorker(
        OpenWorkerDocument document) =>
        new(document.Provenance.ShellRevision, null, null, document);

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
