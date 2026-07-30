using System.Collections.Immutable;
using System.Security.Cryptography;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CommandLine.Contracts.Product;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Generation.Console;
using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;
using Orbyss.ProgramKit.DotNet.Inputs;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.OpenConsole.Contracts.Validation;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>
/// Exact-project Console input materializer with no restore, scan, or semantic
/// inference behavior.
/// </summary>
public sealed class ConsoleInputMaterializer : IConsoleInputMaterializer
{
    private const string AuthoringMarker =
        ".agent-capabilities/authoring-workspace.json";
    private const string RequestSchema =
        "pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.1";
    private const string LockSchema =
        "pkid:schema:program-kit:dotnet-console-input-materialization-lock@0.1.0-alpha.1";
    private const string LockFile =
        ".program-kit-console-inputs.lock.json";
    private static readonly SemanticVersion ContractVersion =
        new("0.1.0-alpha.1");
    private readonly ICommandFileSystem fileSystem;
    private readonly ICommandProcessRunner processRunner;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly IDotNetShellValidator shellValidator;
    private readonly IProgramKitSemanticValidator<OpenConsoleDocument>
        openConsoleValidator;
    private readonly IDotNetConsoleBindingValidator bindingValidator;
    private readonly IDotNetConsoleMetadataInspector metadataInspector;
    private readonly IDotNetConsoleIntegrationAssemblyInspector
        integrationInspector;

    /// <summary>Initializes every explicit materialization collaborator.</summary>
    public ConsoleInputMaterializer(
        ICommandFileSystem fileSystem,
        ICommandProcessRunner processRunner,
        IProgramKitJsonSerializer serializer,
        IDotNetShellValidator shellValidator,
        IProgramKitSemanticValidator<OpenConsoleDocument>
            openConsoleValidator,
        IDotNetConsoleBindingValidator bindingValidator,
        IDotNetConsoleMetadataInspector metadataInspector,
        IDotNetConsoleIntegrationAssemblyInspector integrationInspector)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.processRunner = processRunner ??
            throw new ArgumentNullException(nameof(processRunner));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
        this.shellValidator = shellValidator ??
            throw new ArgumentNullException(nameof(shellValidator));
        this.openConsoleValidator = openConsoleValidator ??
            throw new ArgumentNullException(nameof(openConsoleValidator));
        this.bindingValidator = bindingValidator ??
            throw new ArgumentNullException(nameof(bindingValidator));
        this.metadataInspector = metadataInspector ??
            throw new ArgumentNullException(nameof(metadataInspector));
        this.integrationInspector = integrationInspector ??
            throw new ArgumentNullException(nameof(integrationInspector));
    }

    /// <inheritdoc />
    public async ValueTask<ConsoleInputMaterializationResult> MaterializeAsync(
        string requestPath,
        string workspaceRoot,
        string outputRoot,
        CancellationToken cancellationToken)
    {
        var paths = PreflightPaths(requestPath, workspaceRoot, outputRoot);
        var requestBytes = await fileSystem.ReadAllBytesAsync(
            paths.RequestPath,
            cancellationToken).ConfigureAwait(false);
        var request = ReadRequest(requestBytes);
        ValidateRequest(request, paths);
        var canonicalRequest = serializer.Write(
            request,
            DotNetJsonProfiles.ShellBootstrap.Reference,
            JsonSerializationLimits.Default).ToArray();
        var requestDigest = LocalOperationHashes.Sha256(canonicalRequest);
        var previous = await VerifyExistingOutputAsync(
            paths.OutputRoot,
            paths.WorkspaceRoot,
            cancellationToken).ConfigureAwait(false);

        var projectPath = LocalOperationPaths.ResolveBelow(
            paths.WorkspaceRoot,
            request.ConsumerProjectPath,
            "The consumer project path");
        EnsureNoReparsePoints(paths.WorkspaceRoot, projectPath);
        await BuildConsumerAsync(
            request,
            paths.WorkspaceRoot,
            projectPath,
            cancellationToken).ConfigureAwait(false);
        var query = await QueryReferencesAsync(
            request,
            paths.WorkspaceRoot,
            projectPath,
            cancellationToken).ConfigureAwait(false);
        var references = ReadReferences(
            projectPath,
            query);
        var targetAssemblyPath = ResolveEvaluatedPath(
            Path.GetDirectoryName(projectPath) ??
                throw InvalidReference(
                    "The selected project has no containing directory."),
            query.TargetAssemblyPath);
        _ = LocalOperationPaths.RelativeTo(
            paths.WorkspaceRoot,
            targetAssemblyPath);
        EnsureNoReparsePoints(
            paths.WorkspaceRoot,
            targetAssemblyPath);
        var candidate = await CreateCandidateAsync(
            request,
            paths,
            requestDigest,
            references,
            targetAssemblyPath,
            cancellationToken).ConfigureAwait(false);
        return await PromoteAsync(
            request,
            paths,
            candidate,
            previous,
            cancellationToken).ConfigureAwait(false);
    }

    private ConsoleInputMaterializationPaths PreflightPaths(
        string requestPath,
        string workspaceRoot,
        string outputRoot)
    {
        try
        {
            var workspace = Path.GetFullPath(workspaceRoot);
            LocalOperationPaths.EnsureSafeRoot(workspace);
            if (!fileSystem.DirectoryExists(workspace))
            {
                throw new InvalidDataException(
                    "The explicit consumer workspace does not exist.");
            }

            if (fileSystem.FileExists(
                    LocalOperationPaths.ResolveBelow(
                        workspace,
                        AuthoringMarker,
                        "The authoring marker path")))
            {
                throw new ConsoleInputMaterializationException(
                    ConsoleInputMaterializationDiagnosticIds
                        .AuthoringWorkspaceRejected,
                    "Program Kit product operations cannot materialize consumer inputs in its authoring workspace.",
                    "/workspace-root");
            }

            var request = Path.GetFullPath(requestPath, workspace);
            LocalOperationPaths.RelativeTo(workspace, request);
            var output = Path.GetFullPath(outputRoot, workspace);
            var relativeOutput = LocalOperationPaths.RelativeTo(
                workspace,
                output);
            LocalOperationPaths.RequireNormalizedRelativePath(
                relativeOutput,
                "The materialization output");
            EnsureNoReparsePoints(workspace, request);
            EnsureNoReparsePoints(
                workspace,
                Path.GetDirectoryName(output) ?? workspace);
            var transaction = string.Concat(output, ".program-kit-transaction");
            var backup = string.Concat(output, ".program-kit-previous");
            if (fileSystem.FileExists(transaction) ||
                fileSystem.DirectoryExists(transaction) ||
                fileSystem.FileExists(backup) ||
                fileSystem.DirectoryExists(backup))
            {
                throw new ConsoleInputMaterializationException(
                    ConsoleInputMaterializationDiagnosticIds.TransactionFailed,
                    "A prior Console input materialization transaction requires bounded cleanup.",
                    "/output");
            }

            return new ConsoleInputMaterializationPaths(
                request,
                workspace,
                output,
                transaction,
                backup);
        }
        catch (ConsoleInputMaterializationException)
        {
            throw;
        }
        catch (Exception exception) when (
            exception is ArgumentException or
                IOException or
                InvalidDataException or
                UnauthorizedAccessException)
        {
            throw new ConsoleInputMaterializationException(
                ConsoleInputMaterializationDiagnosticIds.UnsafePath,
                exception.Message,
                "/workspace-root");
        }
    }

    private DotNetConsoleInputMaterializationRequest ReadRequest(
        ReadOnlyMemory<byte> requestBytes)
    {
        try
        {
            return serializer.Read<DotNetConsoleInputMaterializationRequest>(
                requestBytes,
                DotNetJsonProfiles.ShellBootstrap.Reference,
                JsonSerializationLimits.Default);
        }
        catch (ProgramKitJsonException exception)
        {
            throw new ConsoleInputMaterializationException(
                ConsoleInputMaterializationDiagnosticIds.InvalidRequest,
                exception.Message,
                PrefixPath("/request", exception.Diagnostic.Path));
        }
        catch (ArgumentException exception)
        {
            throw new ConsoleInputMaterializationException(
                ConsoleInputMaterializationDiagnosticIds.InvalidRequest,
                exception.Message,
                "/request");
        }
    }

    private static string PrefixPath(string prefix, string path) =>
        string.IsNullOrEmpty(path)
            ? prefix
            : string.Concat(prefix, path);

    private void ValidateRequest(
        DotNetConsoleInputMaterializationRequest request,
        ConsoleInputMaterializationPaths paths)
    {
        if (!string.Equals(request.Schema, RequestSchema, StringComparison.Ordinal) ||
            request.Version != ContractVersion ||
            request.TargetFramework != "net10.0" ||
            request.Configuration is not ("Debug" or "Release") ||
            request.Platform != "AnyCPU" ||
            string.IsNullOrWhiteSpace(request.ConsumerProjectName) ||
            request.SuppliedArtifacts.IsDefaultOrEmpty)
        {
            throw InvalidRequest(
                "The request must initialize the exact alpha.1, net10.0, Debug/Release, AnyCPU contract.");
        }

        try
        {
            LocalOperationPaths.RequireNormalizedRelativePath(
                request.ConsumerProjectPath,
                "The consumer project path");
            if (!request.ConsumerProjectPath.EndsWith(
                    ".csproj",
                    StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidDataException(
                    "The consumer project path must select one .csproj.");
            }

            var suppliedKeys = new HashSet<string>(StringComparer.Ordinal);
            var suppliedRevisions = new HashSet<string>(StringComparer.Ordinal);
            foreach (var supplied in request.SuppliedArtifacts)
            {
                LocalOperationPaths.RequireNormalizedRelativePath(
                    supplied.WorkspaceRelativePath,
                    "A supplied workspace path");
                LocalOperationPaths.RequireNormalizedRelativePath(
                    supplied.OutputRelativePath,
                    "A supplied output path");
                EnsureUnreservedOutput(supplied.OutputRelativePath);
                if (!suppliedKeys.Add(supplied.OutputRelativePath) ||
                    !suppliedRevisions.Add(Exact(supplied.Revision)))
                {
                    throw new InvalidDataException(
                        "Supplied artifact paths and revisions must be unique.");
                }
            }

            RequireSupplied(
                request,
                request.Shell.InputVersionMapRevision);
            RequireSupplied(
                request,
                request.Shell.InputVersionSelectionRevision);
        }
        catch (Exception exception) when (
            exception is ArgumentException or InvalidDataException)
        {
            throw InvalidRequest(exception.Message);
        }

        var hosts = request.Shell.Hosts
            .Where(host =>
                host.Identity == request.HostIdentity &&
                host.Kind == DotNetHostKind.Console)
            .ToArray();
        if (hosts.Length != 1 ||
            request.OpenConsole.HostRevision.Identity !=
                request.HostIdentity ||
            request.OpenConsole.HostRevision.Version != hosts[0].Version)
        {
            throw InvalidRequest(
                "The request must select exactly one Console host and its exact declared host revision.");
        }

        EnsureValid(
            shellValidator.Validate(request.Shell),
            "The supplied shell intent is invalid.");
        _ = paths;
    }

    private async ValueTask BuildConsumerAsync(
        DotNetConsoleInputMaterializationRequest request,
        string workspaceRoot,
        string projectPath,
        CancellationToken cancellationToken)
    {
        var result = await processRunner.RunAsync(
            new CommandProcessRequest(
                "dotnet",
                workspaceRoot,
                BuildArguments(request, projectPath),
                ProcessEnvironment()),
            cancellationToken).ConfigureAwait(false);
        if (result.ExitCode != 0)
        {
            throw ProcessFailure(
                ConsoleInputMaterializationDiagnosticIds.BuildFailed,
                "The exact no-restore consumer project build failed.",
                "/consumerProjectPath",
                result);
        }
    }

    private async ValueTask<MsBuildReferenceQueryResult> QueryReferencesAsync(
        DotNetConsoleInputMaterializationRequest request,
        string workspaceRoot,
        string projectPath,
        CancellationToken cancellationToken)
    {
        var result = await processRunner.RunAsync(
            new CommandProcessRequest(
                "dotnet",
                workspaceRoot,
                QueryArguments(request, projectPath),
                ProcessEnvironment()),
            cancellationToken).ConfigureAwait(false);
        if (result.ExitCode != 0)
        {
            throw ProcessFailure(
                ConsoleInputMaterializationDiagnosticIds.ReferenceQueryFailed,
                "The exact MSBuild reference query failed.",
                "/referenceQuery",
                result);
        }

        return MsBuildReferenceQueryParser.Parse(result.StandardOutput);
    }

    private static ImmutableArray<ManagedAssemblyReference> ReadReferences(
        string projectPath,
        MsBuildReferenceQueryResult query)
    {
        var projectRoot = Path.GetDirectoryName(projectPath) ??
            throw InvalidReference(
                "The selected project has no containing directory.");
        var target = ResolveEvaluatedPath(
            projectRoot,
            query.TargetReferencePath);
        var comparer = OperatingSystem.IsWindows()
            ? StringComparer.OrdinalIgnoreCase
            : StringComparer.Ordinal;
        HashSet<string> queryPaths = new(comparer);
        var references = ImmutableArray.CreateBuilder<ManagedAssemblyReference>();
        foreach (var value in query.CompilationReferencePaths)
        {
            var path = ResolveEvaluatedPath(projectRoot, value);
            if (!queryPaths.Add(path))
            {
                throw InvalidReference(
                    "MSBuild returned a duplicate compilation reference path.");
            }

            references.Add(ManagedAssemblyReferenceReader.Read(
                path,
                consumer: false));
        }

        var targetOccurrences = references.Count(reference =>
            comparer.Equals(reference.FullPath, target));
        if (targetOccurrences > 1)
        {
            throw InvalidReference(
                "The consumer reference assembly occurs more than once.");
        }

        if (targetOccurrences == 1)
        {
            var index = references
                .Select((reference, position) => (reference, position))
                .Single(item => comparer.Equals(
                    item.reference.FullPath,
                    target)).position;
            references[index] = references[index] with { Consumer = true };
        }
        else
        {
            references.Add(ManagedAssemblyReferenceReader.Read(
                target,
                consumer: true));
        }

        var groups = references
            .GroupBy(
                static reference => reference.AssemblyIdentity,
                StringComparer.Ordinal)
            .ToArray();
        foreach (var group in groups)
        {
            if (group.Select(static item => item.Digest.Value)
                .Distinct(StringComparer.Ordinal).Count() != 1)
            {
                throw InvalidReference(
                    "One managed assembly identity resolved to divergent bytes.");
            }
        }

        var collapsed = groups
            .Select(group =>
            {
                var selected = group
                    .OrderBy(static item => item.FullPath, StringComparer.Ordinal)
                    .First();
                return selected with
                {
                    Consumer = group.Any(static item => item.Consumer),
                };
            })
            .OrderBy(static item => item.AssemblyIdentity, StringComparer.Ordinal)
            .ThenBy(static item => item.Digest.Value, StringComparer.Ordinal)
            .ToImmutableArray();
        if (collapsed.Count(static reference => reference.Consumer) != 1)
        {
            throw InvalidReference(
                "The evaluated closure must contain exactly one consumer reference assembly.");
        }

        return collapsed;
    }

    private async ValueTask<ConsoleInputMaterializationCandidate>
        CreateCandidateAsync(
            DotNetConsoleInputMaterializationRequest request,
        ConsoleInputMaterializationPaths paths,
        Sha256Digest requestDigest,
        ImmutableArray<ManagedAssemblyReference> references,
        string targetAssemblyPath,
        CancellationToken cancellationToken)
    {
        var profile = DotNetJsonProfiles.ShellBootstrap.Reference;
        var limits = JsonSerializationLimits.Default;
        var files = ImmutableArray.CreateBuilder<ConsoleInputMaterializedFile>();
        var inputs = ImmutableArray.CreateBuilder<DotNetArtifactInputEntry>();
        foreach (var supplied in request.SuppliedArtifacts)
        {
            var source = LocalOperationPaths.ResolveBelow(
                paths.WorkspaceRoot,
                supplied.WorkspaceRelativePath,
                "A supplied artifact path");
            EnsureNoReparsePoints(paths.WorkspaceRoot, source);
            var bytes = await fileSystem.ReadAllBytesAsync(
                source,
                cancellationToken).ConfigureAwait(false);
            if (LocalOperationHashes.Sha256(bytes.Span) !=
                supplied.Revision.Digest)
            {
                throw InvalidRequest(
                    "A supplied artifact digest is stale or mismatched.");
            }

            files.Add(
                new ConsoleInputMaterializedFile(
                    supplied.OutputRelativePath,
                    bytes));
            inputs.Add(
                new DotNetArtifactInputEntry(
                    supplied.Revision,
                    supplied.OutputRelativePath));
        }

        var shellBytes = serializer.Write(
            request.Shell,
            profile,
            limits).ToArray();
        var shellRevision = Revision(
            request,
            "shell",
            request.Shell.Version,
            shellBytes);
        var openConsole = CreateOpenConsole(request, shellRevision);
        EnsureValid(
            openConsoleValidator.Validate(openConsole),
            "The supplied Open Console intent is invalid.");
        var selectedHost = request.Shell.Hosts.Single(host =>
            host.Identity == request.HostIdentity &&
            host.Kind == DotNetHostKind.Console);
        if (!DotNetConsoleProjectionValidator.IsExact(
                shellRevision,
                selectedHost,
                openConsole))
        {
            throw InvalidRequest(
                "The Open Console intent must bind the selected shell, host, generator, operations, and typed contract sets exactly.");
        }

        var openConsoleBytes = serializer.Write(
            openConsole,
            profile,
            limits).ToArray();
        var openConsoleRevision = Revision(
            request,
            "document",
            openConsole.DocumentVersion,
            openConsoleBytes);

        var materializedReferences = references
            .Select(reference => MaterializedReference(request, reference))
            .ToImmutableArray();
        var consumer = materializedReferences.Single(
            static reference => reference.Consumer);
        var consumerSource = references.Single(
            static reference => reference.Consumer);
        var binding = new DotNetConsoleBindingDocument(
            request.Binding.Schema,
            request.Binding.Version,
            openConsoleRevision,
            new DotNetConsoleConsumerProject(
                request.ConsumerProjectIdentity,
                request.ConsumerProjectName,
                request.ConsumerProjectPath,
                request.TargetFramework,
                consumerSource.Name,
                consumer.RelativePath,
                consumer.Revision.Digest),
            request.Binding.FeatureType,
            request.Binding.ValidationResultType,
            request.Binding.Operations);
        EnsureValid(
            bindingValidator.Validate(binding, openConsole),
            "The supplied Console binding intent is invalid.");
        var metadata = metadataInspector.Inspect(
            binding,
            consumerSource.FullPath);
        if (!metadata.IsValid)
        {
            throw new ConsoleInputMaterializationException(
                ConsoleInputMaterializationDiagnosticIds
                    .InvalidIntegrationAssembly,
                metadata.Diagnostics[0].Message,
                metadata.Diagnostics[0].Path);
        }

        EnsureValid(
            integrationInspector.Inspect(
                binding,
                targetAssemblyPath),
            "The Console integration assembly does not own the complete handler implementation seam.",
            ConsoleInputMaterializationDiagnosticIds
                .InvalidIntegrationAssembly);
        var bindingBytes = serializer.Write(
            binding,
            profile,
            limits).ToArray();
        var bindingRevision = Revision(
            request,
            "binding",
            binding.Version,
            bindingBytes);

        files.Add(new("shell.json", shellBytes));
        files.Add(new("open-console.json", openConsoleBytes));
        inputs.Add(new(openConsoleRevision, "open-console.json"));
        files.Add(new("console-binding.json", bindingBytes));
        inputs.Add(new(bindingRevision, "console-binding.json"));
        foreach (var reference in references.Zip(materializedReferences))
        {
            var currentBytes = await fileSystem.ReadAllBytesAsync(
                reference.First.FullPath,
                cancellationToken).ConfigureAwait(false);
            if (LocalOperationHashes.Sha256(currentBytes.Span) !=
                reference.Second.Revision.Digest)
            {
                throw InvalidReference(
                    "An evaluated reference changed during materialization.");
            }

            files.Add(
                new ConsoleInputMaterializedFile(
                    reference.Second.RelativePath,
                    reference.First.Content));
            inputs.Add(
                new DotNetArtifactInputEntry(
                    reference.Second.Revision,
                    reference.Second.RelativePath));
        }

        var manifest = new DotNetArtifactInputManifestAlpha1(
            "pkid:schema:program-kit:dotnet-artifact-input-manifest@0.1.0-alpha.1",
            ContractVersion,
            inputs
                .OrderBy(
                    static input => Exact(input.Revision),
                    StringComparer.Ordinal)
                .ToImmutableArray(),
            [new DotNetHostDocumentInput(
                request.HostIdentity,
                openConsoleRevision)],
            [
                new DotNetConsoleGenerationInputBinding(
                    request.HostIdentity,
                    bindingRevision,
                    consumer.Revision,
                    materializedReferences
                        .Select(static reference => reference.Revision)
                        .OrderBy(Exact, StringComparer.Ordinal)
                        .ToImmutableArray()),
            ]);
        var manifestBytes = serializer.Write(
            manifest,
            profile,
            limits).ToArray();
        files.Add(new("artifact-manifest.json", manifestBytes));

        var uniqueFiles = files
            .GroupBy(static file => file.RelativePath, StringComparer.Ordinal)
            .ToArray();
        if (uniqueFiles.Any(static group => group.Count() != 1))
        {
            throw InvalidRequest(
                "Materialized output paths collide.");
        }

        var orderedFiles = uniqueFiles
            .Select(static group => group.Single())
            .OrderBy(static file => file.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
        var outputs = orderedFiles
            .Select(file => new DotNetConsoleMaterializedOutput(
                file.RelativePath,
                LocalOperationHashes.Sha256(file.Content.Span)))
            .ToImmutableArray();
        var orderedMaterializedReferences = materializedReferences
            .OrderBy(
                static reference => Exact(reference.Revision),
                StringComparer.Ordinal)
            .ToImmutableArray();
        var lockDocument = new DotNetConsoleInputMaterializationLock(
            LockSchema,
            ContractVersion,
            new SemanticVersion(ProgramKitProductInfo.Version),
            requestDigest,
            RelativePath(paths.OutputRoot, paths.WorkspaceRoot),
            request.ConsumerProjectPath,
            request.TargetFramework,
            request.Configuration,
            request.Platform,
            BuildContractArguments(request),
            consumer,
            orderedMaterializedReferences,
            LocalOperationHashes.Sha256(manifestBytes),
            outputs);
        var lockBytes = serializer.Write(
            lockDocument,
            profile,
            limits).ToArray();
        orderedFiles =
        [
            .. orderedFiles,
            new ConsoleInputMaterializedFile(LockFile, lockBytes),
        ];
        return new ConsoleInputMaterializationCandidate(
            lockDocument,
            orderedFiles,
            orderedMaterializedReferences
                .Select(static reference => reference.RelativePath)
                .ToImmutableArray());
    }

    private async ValueTask<DotNetConsoleInputMaterializationLock?>
        VerifyExistingOutputAsync(
            string outputRoot,
            string workspaceRoot,
            CancellationToken cancellationToken)
    {
        if (!fileSystem.DirectoryExists(outputRoot))
        {
            if (fileSystem.FileExists(outputRoot))
            {
                throw OwnershipFailure(
                    "The explicit materialization output is an existing file.");
            }

            return null;
        }

        EnsureNoReparsePoints(outputRoot, outputRoot);
        var lockPath = Path.Combine(outputRoot, LockFile);
        if (!fileSystem.FileExists(lockPath))
        {
            throw OwnershipFailure(
                "The existing materialization output has no Program Kit ownership lock.");
        }

        DotNetConsoleInputMaterializationLock existing;
        try
        {
            var lockBytes = await fileSystem.ReadAllBytesAsync(
                lockPath,
                cancellationToken).ConfigureAwait(false);
            existing =
                serializer.Read<DotNetConsoleInputMaterializationLock>(
                    lockBytes,
                    DotNetJsonProfiles.ShellBootstrap.Reference,
                    JsonSerializationLimits.Default);
        }
        catch (Exception exception) when (
            exception is ProgramKitJsonException or ArgumentException)
        {
            throw OwnershipFailure(
                string.Concat(
                    "The existing materialization lock is invalid. ",
                    exception.Message));
        }

        if (existing.Schema != LockSchema ||
            existing.Version != ContractVersion ||
            existing.ProgramKitVersion.Value != ProgramKitProductInfo.Version ||
            existing.WorkspaceRootRelativePath !=
                RelativePath(outputRoot, workspaceRoot) ||
            existing.Outputs.IsDefaultOrEmpty)
        {
            throw OwnershipFailure(
                "The existing materialization lock is unsupported or version-mismatched.");
        }

        var expectedBuildArguments = ImmutableArray.Create(
            "build",
            existing.ConsumerProjectPath,
            "--configuration",
            existing.Configuration,
            "--framework",
            existing.TargetFramework,
            "--no-restore",
            "--verbosity",
            "minimal",
            string.Concat("-property:Platform=", existing.Platform));
        var referenceKeys = existing.CompilationReferences
            .Select(static reference => Exact(reference.Revision))
            .ToArray();
        var outputPaths = existing.Outputs
            .Select(static output => output.RelativePath)
            .ToArray();
        if (!existing.BuildArguments.SequenceEqual(
                expectedBuildArguments,
                StringComparer.Ordinal) ||
            referenceKeys.Distinct(StringComparer.Ordinal).Count() !=
                referenceKeys.Length ||
            !referenceKeys.SequenceEqual(
                referenceKeys.Order(StringComparer.Ordinal),
                StringComparer.Ordinal) ||
            existing.CompilationReferences.Count(
                static reference => reference.Consumer) != 1 ||
            existing.CompilationReferences.Count(reference =>
                reference == existing.ConsumerReference) != 1 ||
            outputPaths.Distinct(StringComparer.Ordinal).Count() !=
                outputPaths.Length ||
            !outputPaths.SequenceEqual(
                outputPaths.Order(StringComparer.Ordinal),
                StringComparer.Ordinal) ||
            existing.Outputs.Count(output =>
                output.RelativePath == "artifact-manifest.json" &&
                output.Digest == existing.ManifestDigest) != 1 ||
            existing.CompilationReferences.Any(reference =>
                existing.Outputs.Count(output =>
                    output.RelativePath == reference.RelativePath &&
                    output.Digest == reference.Revision.Digest) != 1))
        {
            throw OwnershipFailure(
                "The existing materialization lock is internally inconsistent.");
        }

        var expected = existing.Outputs
            .Select(static output => output.RelativePath)
            .Append(LockFile)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var actual = fileSystem.EnumerateFiles(outputRoot)
            .Select(path => LocalOperationPaths.RelativeTo(outputRoot, path))
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!expected.SequenceEqual(actual, StringComparer.Ordinal))
        {
            throw OwnershipFailure(
                "The existing materialization output contains missing or unexpected files.");
        }

        foreach (var output in existing.Outputs)
        {
            var path = LocalOperationPaths.ResolveBelow(
                outputRoot,
                output.RelativePath,
                "An owned materialization path");
            var bytes = await fileSystem.ReadAllBytesAsync(
                path,
                cancellationToken).ConfigureAwait(false);
            if (LocalOperationHashes.Sha256(bytes.Span) != output.Digest)
            {
                throw OwnershipFailure(
                    "An existing Program Kit-owned materialization file was modified.");
            }
        }

        return existing;
    }

    private async ValueTask<ConsoleInputMaterializationResult> PromoteAsync(
        DotNetConsoleInputMaterializationRequest request,
        ConsoleInputMaterializationPaths paths,
        ConsoleInputMaterializationCandidate candidate,
        DotNetConsoleInputMaterializationLock? previous,
        CancellationToken cancellationToken)
    {
        fileSystem.CreateDirectory(paths.TransactionRoot);
        try
        {
            foreach (var file in candidate.Files)
            {
                var path = LocalOperationPaths.ResolveBelow(
                    paths.TransactionRoot,
                    file.RelativePath,
                    "A materialized output path");
                await fileSystem.WriteAllBytesAsync(
                    path,
                    file.Content,
                    cancellationToken).ConfigureAwait(false);
            }

            foreach (var relativePath in candidate.ReadOnlyRelativePaths)
            {
                fileSystem.SetReadOnly(
                    LocalOperationPaths.ResolveBelow(
                        paths.TransactionRoot,
                        relativePath,
                        "A materialized reference path"),
                    isReadOnly: true);
            }

            await VerifyCandidateAsync(
                paths.TransactionRoot,
                candidate,
                cancellationToken).ConfigureAwait(false);
            if (previous is not null &&
                await DirectoriesEqualAsync(
                    paths.OutputRoot,
                    paths.TransactionRoot,
                    cancellationToken).ConfigureAwait(false))
            {
                fileSystem.DeleteDirectory(paths.TransactionRoot);
                return Result(
                    ConsoleInputMaterializationStatus.Unchanged,
                    request,
                    paths.OutputRoot);
            }

            if (previous is null)
            {
                fileSystem.MoveDirectory(
                    paths.TransactionRoot,
                    paths.OutputRoot);
                return Result(
                    ConsoleInputMaterializationStatus.Created,
                    request,
                    paths.OutputRoot);
            }

            fileSystem.MoveDirectory(paths.OutputRoot, paths.BackupRoot);
            try
            {
                fileSystem.MoveDirectory(
                    paths.TransactionRoot,
                    paths.OutputRoot);
                fileSystem.DeleteDirectory(paths.BackupRoot);
            }
            catch
            {
                if (!fileSystem.DirectoryExists(paths.OutputRoot) &&
                    fileSystem.DirectoryExists(paths.BackupRoot))
                {
                    fileSystem.MoveDirectory(
                        paths.BackupRoot,
                        paths.OutputRoot);
                }

                throw;
            }

            return Result(
                ConsoleInputMaterializationStatus.Updated,
                request,
                paths.OutputRoot);
        }
        catch (ConsoleInputMaterializationException)
        {
            fileSystem.DeleteDirectory(paths.TransactionRoot);
            throw;
        }
        catch (OperationCanceledException)
        {
            fileSystem.DeleteDirectory(paths.TransactionRoot);
            throw;
        }
        catch (Exception exception) when (
            exception is IOException or UnauthorizedAccessException)
        {
            fileSystem.DeleteDirectory(paths.TransactionRoot);
            throw new ConsoleInputMaterializationException(
                ConsoleInputMaterializationDiagnosticIds.TransactionFailed,
                exception.Message,
                "/output");
        }
    }

    private async ValueTask VerifyCandidateAsync(
        string root,
        ConsoleInputMaterializationCandidate candidate,
        CancellationToken cancellationToken)
    {
        var actual = fileSystem.EnumerateFiles(root)
            .Select(path => LocalOperationPaths.RelativeTo(root, path))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var expected = candidate.Files
            .Select(static file => file.RelativePath)
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!actual.SequenceEqual(expected, StringComparer.Ordinal))
        {
            throw new ConsoleInputMaterializationException(
                ConsoleInputMaterializationDiagnosticIds.TransactionFailed,
                "The staged materialization file closure is incomplete.",
                "/output");
        }

        foreach (var file in candidate.Files)
        {
            var bytes = await fileSystem.ReadAllBytesAsync(
                LocalOperationPaths.ResolveBelow(
                    root,
                    file.RelativePath,
                    "A staged materialization path"),
                cancellationToken).ConfigureAwait(false);
            if (!bytes.Span.SequenceEqual(file.Content.Span))
            {
                throw new ConsoleInputMaterializationException(
                    ConsoleInputMaterializationDiagnosticIds.TransactionFailed,
                    "A staged materialization file changed before promotion.",
                    file.RelativePath);
            }
        }
    }

    private async ValueTask<bool> DirectoriesEqualAsync(
        string left,
        string right,
        CancellationToken cancellationToken)
    {
        var leftFiles = fileSystem.EnumerateFiles(left)
            .Select(path => LocalOperationPaths.RelativeTo(left, path))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var rightFiles = fileSystem.EnumerateFiles(right)
            .Select(path => LocalOperationPaths.RelativeTo(right, path))
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!leftFiles.SequenceEqual(rightFiles, StringComparer.Ordinal))
        {
            return false;
        }

        foreach (var relative in leftFiles)
        {
            var leftBytes = await fileSystem.ReadAllBytesAsync(
                LocalOperationPaths.ResolveBelow(left, relative, "An owned path"),
                cancellationToken).ConfigureAwait(false);
            var rightBytes = await fileSystem.ReadAllBytesAsync(
                LocalOperationPaths.ResolveBelow(right, relative, "A staged path"),
                cancellationToken).ConfigureAwait(false);
            if (!leftBytes.Span.SequenceEqual(rightBytes.Span))
            {
                return false;
            }
        }

        return true;
    }

    private static OpenConsoleDocument CreateOpenConsole(
        DotNetConsoleInputMaterializationRequest request,
        ArtifactReference shellRevision) =>
        new(
            request.OpenConsole.Schema,
            request.OpenConsole.DocumentVersion,
            request.OpenConsole.Info,
            request.OpenConsole.HostRevision,
            request.OpenConsole.Parsing,
            request.OpenConsole.HostExitCodeRoles,
            request.OpenConsole.GlobalOptions,
            request.OpenConsole.Commands,
            request.OpenConsole.Help,
            request.OpenConsole.Completion,
            request.OpenConsole.Compatibility,
            new OpenConsoleProvenance(
                shellRevision,
                request.OpenConsole.GeneratorRevision,
                request.OpenConsole.OperationRevisions));

    private static DotNetConsoleMaterializedReference MaterializedReference(
        DotNetConsoleInputMaterializationRequest request,
        ManagedAssemblyReference reference)
    {
        var version = new SemanticVersion(
            string.Concat(
                Math.Max(reference.AssemblyVersion.Major, 0),
                ".",
                Math.Max(reference.AssemblyVersion.Minor, 0),
                ".",
                Math.Max(reference.AssemblyVersion.Build, 0)));
        var revision = new ArtifactReference(
            DerivedIdentity(
                request,
                "assembly",
                string.Concat(
                    Slug(reference.Name),
                    "-",
                    version.Value.Replace('.', '-'))),
            version,
            reference.Digest);
        var relativePath = string.Concat(
            "references/",
            reference.Digest.Value[7..23],
            "/",
            SafeFileName(reference.Name),
            ".dll");
        return new DotNetConsoleMaterializedReference(
            reference.AssemblyIdentity,
            revision,
            relativePath,
            reference.Consumer);
    }

    private static ArtifactReference Revision(
        DotNetConsoleInputMaterializationRequest request,
        string kind,
        SemanticVersion version,
        ReadOnlySpan<byte> bytes) =>
        new(
            DerivedIdentity(request, kind, null),
            version,
            LocalOperationHashes.Sha256(bytes));

    private static ProgramKitIdentifier DerivedIdentity(
        DotNetConsoleInputMaterializationRequest request,
        string kind,
        string? name)
    {
        var segments = request.OutputSetIdentity.Value.Split(':');
        var suffix = name ?? segments[3];
        return new ProgramKitIdentifier(
            string.Concat(
                "pkid:",
                kind,
                ":",
                segments[2],
                ":",
                suffix));
    }

    private static string Slug(string value)
    {
        var characters = value.ToLowerInvariant()
            .Select(static character =>
                char.IsAsciiLetterOrDigit(character)
                    ? character
                    : '-')
            .ToArray();
        var transformed = new string(characters);
        var result = transformed.Trim('-');
        while (result.Contains("--", StringComparison.Ordinal))
        {
            result = result.Replace("--", "-", StringComparison.Ordinal);
        }

        return result.Length <= 80
            ? result
            : result[..80].TrimEnd('-');
    }

    private static string SafeFileName(string value) =>
        new(
            value.Select(static character =>
                char.IsAsciiLetterOrDigit(character) ||
                character is '.' or '-' or '_'
                    ? character
                    : '_').ToArray());

    private static string ResolveEvaluatedPath(
        string projectRoot,
        string value) =>
        Path.GetFullPath(value, projectRoot);

    private static void RequireSupplied(
        DotNetConsoleInputMaterializationRequest request,
        ArtifactReference revision)
    {
        if (request.SuppliedArtifacts.Count(item =>
                item.Revision == revision) != 1)
        {
            throw new InvalidDataException(
                "The shell version-map and version-selection revisions must each resolve to one supplied artifact.");
        }
    }

    private static void EnsureUnreservedOutput(string relativePath)
    {
        if (relativePath is
                "shell.json" or
                "open-console.json" or
                "console-binding.json" or
                "artifact-manifest.json" or
                LockFile ||
            relativePath.StartsWith(
                "references/",
                StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                "A supplied artifact collides with a Program Kit-owned output path.");
        }
    }

    private static void EnsureNoReparsePoints(string root, string path)
    {
        var relative = Path.GetRelativePath(
            Path.GetFullPath(root),
            Path.GetFullPath(path));
        var current = Path.GetFullPath(root);
        if (File.Exists(current) || Directory.Exists(current))
        {
            RejectReparse(current);
        }

        foreach (var segment in relative.Split(
                     Path.DirectorySeparatorChar,
                     StringSplitOptions.RemoveEmptyEntries))
        {
            if (segment is "." or "..")
            {
                continue;
            }

            current = Path.Combine(current, segment);
            if (File.Exists(current) || Directory.Exists(current))
            {
                RejectReparse(current);
            }
        }
    }

    private static void RejectReparse(string path)
    {
        if (File.GetAttributes(path).HasFlag(FileAttributes.ReparsePoint))
        {
            throw new InvalidDataException(
                "Explicit materialization paths cannot traverse a reparse point.");
        }
    }

    private static ImmutableArray<string> BuildArguments(
        DotNetConsoleInputMaterializationRequest request,
        string projectPath) =>
        [
            "build",
            projectPath,
            "--configuration",
            request.Configuration,
            "--framework",
            request.TargetFramework,
            "--no-restore",
            "--verbosity",
            "minimal",
            string.Concat("-property:Platform=", request.Platform),
        ];

    private static ImmutableArray<string> BuildContractArguments(
        DotNetConsoleInputMaterializationRequest request) =>
        [
            "build",
            request.ConsumerProjectPath,
            "--configuration",
            request.Configuration,
            "--framework",
            request.TargetFramework,
            "--no-restore",
            "--verbosity",
            "minimal",
            string.Concat("-property:Platform=", request.Platform),
        ];

    private static ImmutableArray<string> QueryArguments(
        DotNetConsoleInputMaterializationRequest request,
        string projectPath) =>
        [
            "msbuild",
            projectPath,
            "-nologo",
            "-target:FindReferenceAssembliesForReferences",
            "-getProperty:TargetPath",
            "-getProperty:TargetRefPath",
            "-getItem:ReferencePathWithRefAssemblies",
            string.Concat("-property:Configuration=", request.Configuration),
            string.Concat("-property:TargetFramework=", request.TargetFramework),
            string.Concat("-property:Platform=", request.Platform),
        ];

    private static ImmutableDictionary<string, string> ProcessEnvironment() =>
        ImmutableDictionary<string, string>.Empty
            .Add("DOTNET_NOLOGO", "1")
            .Add("DOTNET_CLI_TELEMETRY_OPTOUT", "1");

    private static void EnsureValid(
        ProgramKitValidationResult result,
        string message,
        string diagnosticId =
            ConsoleInputMaterializationDiagnosticIds.InvalidRequest)
    {
        if (!result.IsValid)
        {
            var diagnostic = result.Diagnostics[0];
            throw new ConsoleInputMaterializationException(
                diagnosticId,
                string.Concat(message, " ", diagnostic.Message),
                diagnostic.Path);
        }
    }

    private static ConsoleInputMaterializationException InvalidRequest(
        string message) =>
        new(
            ConsoleInputMaterializationDiagnosticIds.InvalidRequest,
            message,
            "/request");

    private static ConsoleInputMaterializationException InvalidReference(
        string message) =>
        new(
            ConsoleInputMaterializationDiagnosticIds.InvalidReferenceClosure,
            message,
            "/referenceQuery");

    private static ConsoleInputMaterializationException OwnershipFailure(
        string message) =>
        new(
            ConsoleInputMaterializationDiagnosticIds.OutputOwnershipConflict,
            message,
            "/output");

    private static ConsoleInputMaterializationException ProcessFailure(
        string id,
        string message,
        string path,
        CommandProcessResult result)
    {
        var detail = string.IsNullOrWhiteSpace(result.StandardError)
            ? result.StandardOutput
            : result.StandardError;
        detail = detail.Trim();
        if (detail.Length > 4096)
        {
            detail = detail[^4096..];
        }

        return new ConsoleInputMaterializationException(
            id,
            string.IsNullOrWhiteSpace(detail)
                ? message
                : string.Concat(message, " ", detail),
            path);
    }

    private static ConsoleInputMaterializationResult Result(
        ConsoleInputMaterializationStatus status,
        DotNetConsoleInputMaterializationRequest request,
        string outputRoot) =>
        new(
            status,
            outputRoot,
            Path.Combine(outputRoot, "shell.json"),
            Path.Combine(outputRoot, "artifact-manifest.json"),
            request.HostIdentity.Value);

    private static string RelativePath(string from, string to) =>
        Path.GetRelativePath(from, to)
            .Replace(Path.DirectorySeparatorChar, '/');

    private static string Exact(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);

}
