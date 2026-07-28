using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Fail-closed deterministic create, compare, replace, and repair orchestration.</summary>
public sealed class DotNetHostRefreshService : IDotNetHostRefreshService
{
    private const string CurrentProgramKitVersion = "0.1.0-alpha.2";
    private const string RequestSchemaVersion = "1.0.0";
    private const string CandidateSuffix = ".program-kit-refresh-candidate";
    private const string TransactionSuffix = ".program-kit-refresh-transaction";
    private readonly IDotNetHostGenerationCommandService generationService;
    private readonly IGeneratedOutputIntegrityVerifier integrityVerifier;
    private readonly ICSharpGateCompilerHarness compilerHarness;
    private readonly IDotNetHostRefreshSerializer refreshSerializer;

    /// <summary>Initializes refresh from existing backed generation, integrity, and build boundaries.</summary>
    public DotNetHostRefreshService(
        IDotNetHostGenerationCommandService generationService,
        IGeneratedOutputIntegrityVerifier integrityVerifier,
        ICSharpGateCompilerHarness compilerHarness,
        IDotNetHostRefreshSerializer refreshSerializer)
    {
        this.generationService = generationService ??
            throw new ArgumentNullException(nameof(generationService));
        this.integrityVerifier = integrityVerifier ??
            throw new ArgumentNullException(nameof(integrityVerifier));
        this.compilerHarness = compilerHarness ??
            throw new ArgumentNullException(nameof(compilerHarness));
        this.refreshSerializer = refreshSerializer ??
            throw new ArgumentNullException(nameof(refreshSerializer));
    }

    /// <inheritdoc />
    public async ValueTask<DotNetHostRefreshResult> RefreshAsync(
        string requestPath,
        bool preview,
        bool buildConsumer,
        bool repairGeneratedOutput,
        CancellationToken cancellationToken)
    {
        var requestFile = Path.GetFullPath(requestPath);
        var requestRoot = Path.GetDirectoryName(requestFile) ??
            throw Input("PKREF001", "The generation request has no parent directory.", "/request");
        DotNetHostGenerationRequestDocument document;
        try
        {
            var bytes = await File.ReadAllBytesAsync(
                requestFile,
                cancellationToken).ConfigureAwait(false);
            document = refreshSerializer.ReadRequest(bytes);
        }
        catch (Exception exception) when (
            exception is IOException or
            UnauthorizedAccessException or
            JsonException)
        {
            throw Input(
                "PKREF001",
                "The generation request is missing, unreadable, or malformed.",
                "/request");
        }

        ValidateDocument(document, buildConsumer);
        var outputRoot = ResolveRelative(
            requestRoot,
            document.OutputRoot,
            "/outputRoot");
        RecoverCompletedTransaction(outputRoot);
        var candidateRoot = string.Concat(outputRoot, CandidateSuffix);
        var candidateAnchor = GeneratedOutputPathPolicy.AnchorPath(candidateRoot);
        if (Directory.Exists(candidateRoot) ||
            File.Exists(candidateRoot) ||
            File.Exists(candidateAnchor) ||
            Directory.Exists(candidateAnchor))
        {
            throw Input(
                "PKREF002",
                "A previous refresh candidate exists and was preserved for inspection.",
                "/outputRoot");
        }

        if (buildConsumer)
        {
            await BuildConsumerAsync(
                requestRoot,
                document.ConsumerBuild!,
                cancellationToken).ConfigureAwait(false);
        }

        var outputParent = Path.GetDirectoryName(outputRoot) ??
            throw Input("PKREF003", "The output root has no parent.", "/outputRoot");
        Directory.CreateDirectory(outputParent);
        try
        {
            _ = await generationService.GenerateAsync(
                new DotNetHostGenerationCommandRequest(
                    ResolveRelative(requestRoot, document.ShellPath, "/shellPath"),
                    document.HostIdentity,
                    ResolveRelative(
                        requestRoot,
                        document.ArtifactManifestPath,
                        "/artifactManifestPath"),
                    candidateRoot,
                    ParseKind(document.Kind)),
                cancellationToken).ConfigureAwait(false);
            var candidateVerification = await integrityVerifier.VerifyAsync(
                candidateRoot,
                cancellationToken).ConfigureAwait(false);
            if (!candidateVerification.IsValid)
            {
                throw Input(
                    "PKREF004",
                    "The generated refresh candidate did not pass its own integrity verification.",
                    "/outputRoot");
            }

            var candidateDigest = await ManifestDigestAsync(
                candidateRoot,
                cancellationToken).ConfigureAwait(false);
            var currentExists =
                Directory.Exists(outputRoot) ||
                File.Exists(outputRoot) ||
                File.Exists(GeneratedOutputPathPolicy.AnchorPath(outputRoot)) ||
                Directory.Exists(GeneratedOutputPathPolicy.AnchorPath(outputRoot));
            if (!currentExists)
            {
                var result = new DotNetHostRefreshResult(
                    "create",
                    document.OutputRoot,
                    candidateDigest,
                    "absent",
                    null);
                if (!preview)
                {
                    PublishCandidate(candidateRoot, outputRoot);
                }

                return result;
            }

            var current = await integrityVerifier.VerifyAsync(
                outputRoot,
                cancellationToken).ConfigureAwait(false);
            if (!current.IsValid)
            {
                var quarantineDigest = await DriftDigestAsync(
                    outputRoot,
                    current,
                    cancellationToken).ConfigureAwait(false);
                if (!repairGeneratedOutput)
                {
                    throw new DotNetHostRefreshException(
                        "PKREF005",
                        CommandExitCode.ConformanceFailure,
                        string.Concat(
                            "Tampered-with Program Kit generated output blocks refresh. ",
                            current.Issues[0].Message),
                        current.Issues[0].Path);
                }

                var result = new DotNetHostRefreshResult(
                    "repair",
                    document.OutputRoot,
                    candidateDigest,
                    "tampered",
                    quarantineDigest);
                if (!preview)
                {
                    RepairFromCandidate(
                        candidateRoot,
                        outputRoot,
                        quarantineDigest);
                }

                return result;
            }

            if (await TreesEqualAsync(
                    candidateRoot,
                    outputRoot,
                    cancellationToken).ConfigureAwait(false))
            {
                return new DotNetHostRefreshResult(
                    "unchanged",
                    document.OutputRoot,
                    candidateDigest,
                    "valid",
                    null);
            }

            var replacement = new DotNetHostRefreshResult(
                "replace",
                document.OutputRoot,
                candidateDigest,
                "valid",
                null);
            if (!preview)
            {
                ReplaceFromCandidate(candidateRoot, outputRoot);
            }

            return replacement;
        }
        finally
        {
            DeleteCandidate(candidateRoot);
        }
    }

    private async ValueTask BuildConsumerAsync(
        string requestRoot,
        DotNetHostConsumerBuildRequest build,
        CancellationToken cancellationToken)
    {
        var workingDirectory = ResolveRelative(
            requestRoot,
            build.WorkingDirectory,
            "/consumerBuild/workingDirectory");
        var projectPath = ResolveRelative(
            requestRoot,
            build.ProjectPath,
            "/consumerBuild/projectPath");
        var result = await compilerHarness.VerifyAsync(
            new CSharpGateVerificationRequest(
                workingDirectory,
                projectPath,
                CSharpGateCommand.Build,
                CSharpGateImplementationBoundary.GeneratedOutput,
                CSharpGateVerificationProfileKind.GeneratedOutput,
                new SemanticVersion("10.0.302"),
                ResolveRelative(
                    requestRoot,
                    build.EvidenceOutputPath,
                    "/consumerBuild/evidenceOutputPath"),
                build.ParticipationReceiptPaths,
                build.ExceptionUseReceiptPaths,
                build.PackagePaths,
                build.MaximumCapturedOutputBytes,
                build.PerformanceBudgetMilliseconds),
            cancellationToken).ConfigureAwait(false);
        if (!result.Succeeded)
        {
            throw new DotNetHostRefreshException(
                "PKREF006",
                CommandExitCode.ConformanceFailure,
                "The explicitly requested consumer build did not conform.",
                "/consumerBuild");
        }
    }

    private static void ValidateDocument(
        DotNetHostGenerationRequestDocument document,
        bool buildConsumer)
    {
        if (!string.Equals(
                document.SchemaVersion,
                RequestSchemaVersion,
                StringComparison.Ordinal))
        {
            throw Input(
                "PKREF007",
                "Only generation request schema version 1.0.0 is supported.",
                "/schemaVersion");
        }

        if (!string.Equals(
                document.ProgramKitVersion,
                CurrentProgramKitVersion,
                StringComparison.Ordinal))
        {
            throw Input(
                "PKREF008",
                "The generation request must select the exact active Program Kit version; refresh never upgrades it.",
                "/programKitVersion");
        }

        _ = ParseKind(document.Kind);
        if (string.IsNullOrWhiteSpace(document.HostIdentity))
        {
            throw Input("PKREF009", "A host identity is required.", "/hostIdentity");
        }

        if (buildConsumer && document.ConsumerBuild is null)
        {
            throw Input(
                "PKREF010",
                "--build-consumer requires exact consumerBuild inputs in the generation request.",
                "/consumerBuild");
        }

        if (document.ConsumerBuild is { } build &&
            (build.ParticipationReceiptPaths.IsDefault ||
             build.ExceptionUseReceiptPaths.IsDefault ||
             build.PackagePaths.IsDefault ||
             !StableRelativePaths(build.ParticipationReceiptPaths) ||
             !StableRelativePaths(build.ExceptionUseReceiptPaths) ||
             !StableRelativePaths(build.PackagePaths) ||
             build.MaximumCapturedOutputBytes is <= 0 or > 1_048_576 ||
             build.PerformanceBudgetMilliseconds <= 0))
        {
            throw Input(
                "PKREF011",
                "Consumer build inputs must be initialized and finitely bounded.",
                "/consumerBuild");
        }
    }

    private static bool StableRelativePaths(
        ImmutableArray<string> paths) =>
        paths
            .All(static path =>
                !string.IsNullOrWhiteSpace(path) &&
                !Path.IsPathRooted(path) &&
                !path.Split('/', '\\').Any(
                    static segment => segment is "." or "..")) &&
        paths.Distinct(StringComparer.Ordinal).Count() == paths.Length &&
        paths.SequenceEqual(paths.Order(StringComparer.Ordinal));

    private static DotNetHostKind ParseKind(string kind) =>
        kind switch
        {
            "api" => DotNetHostKind.Api,
            "console" => DotNetHostKind.Console,
            "worker" => DotNetHostKind.Worker,
            _ => throw Input(
                "PKREF012",
                "The generation request kind must be api, console, or worker.",
                "/kind"),
        };

    private static string ResolveRelative(
        string requestRoot,
        string path,
        string diagnosticPath)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            Path.IsPathRooted(path) ||
            path.Split('/', '\\').Any(static segment => segment is "." or ".."))
        {
            throw Input(
                "PKREF013",
                "Generation request paths must be non-empty, relative, and traversal-free.",
                diagnosticPath);
        }

        var root = Path.GetFullPath(requestRoot);
        var resolved = Path.GetFullPath(Path.Combine(root, path));
        var prefix = string.Concat(
            root.TrimEnd(
                Path.DirectorySeparatorChar,
                Path.AltDirectorySeparatorChar),
            Path.DirectorySeparatorChar);
        if (!resolved.StartsWith(
                prefix,
                OperatingSystem.IsWindows()
                    ? StringComparison.OrdinalIgnoreCase
                    : StringComparison.Ordinal))
        {
            throw Input(
                "PKREF013",
                "A generation request path escapes its request directory.",
                diagnosticPath);
        }

        return resolved;
    }

    private static async ValueTask<string> ManifestDigestAsync(
        string root,
        CancellationToken cancellationToken)
    {
        var path = GeneratedOutputPathPolicy.ResolveUnderRoot(
            root,
            GeneratedOutputIntegrityConstants.ManifestRelativePath,
            allowManifest: true);
        await using var stream = File.OpenRead(path);
        return string.Concat(
            "sha256:",
            Convert.ToHexStringLower(
                await SHA256.HashDataAsync(
                    stream,
                    cancellationToken).ConfigureAwait(false)));
    }

    private static async ValueTask<bool> TreesEqualAsync(
        string left,
        string right,
        CancellationToken cancellationToken)
    {
        var leftFiles = Directory.EnumerateFiles(
                left,
                "*",
                SearchOption.AllDirectories)
            .Select(path => Path.GetRelativePath(left, path).Replace('\\', '/'))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var rightFiles = Directory.EnumerateFiles(
                right,
                "*",
                SearchOption.AllDirectories)
            .Select(path => Path.GetRelativePath(right, path).Replace('\\', '/'))
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!leftFiles.SequenceEqual(rightFiles, StringComparer.Ordinal))
        {
            return false;
        }

        foreach (var relative in leftFiles)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var leftBytes = await File.ReadAllBytesAsync(
                Path.Combine(left, relative.Replace('/', Path.DirectorySeparatorChar)),
                cancellationToken).ConfigureAwait(false);
            var rightBytes = await File.ReadAllBytesAsync(
                Path.Combine(right, relative.Replace('/', Path.DirectorySeparatorChar)),
                cancellationToken).ConfigureAwait(false);
            if (!leftBytes.AsSpan().SequenceEqual(rightBytes))
            {
                return false;
            }
        }

        var leftAnchor = await File.ReadAllBytesAsync(
            GeneratedOutputPathPolicy.AnchorPath(left),
            cancellationToken).ConfigureAwait(false);
        var rightAnchor = await File.ReadAllBytesAsync(
            GeneratedOutputPathPolicy.AnchorPath(right),
            cancellationToken).ConfigureAwait(false);
        return leftAnchor.AsSpan().SequenceEqual(rightAnchor);
    }

    private static void PublishCandidate(string candidateRoot, string outputRoot)
    {
        Directory.Move(candidateRoot, outputRoot);
        File.Move(
            GeneratedOutputPathPolicy.AnchorPath(candidateRoot),
            GeneratedOutputPathPolicy.AnchorPath(outputRoot));
    }

    private void ReplaceFromCandidate(string candidateRoot, string outputRoot)
    {
        var transaction = string.Concat(outputRoot, TransactionSuffix);
        if (Directory.Exists(transaction) || File.Exists(transaction))
        {
            throw Input(
                "PKREF014",
                "An existing refresh transaction was preserved.",
                "/outputRoot");
        }

        Directory.CreateDirectory(transaction);
        var backupRoot = Path.Combine(transaction, "root");
        var backupAnchor = Path.Combine(transaction, "anchor.json");
        Directory.Move(outputRoot, backupRoot);
        File.Move(GeneratedOutputPathPolicy.AnchorPath(outputRoot), backupAnchor);
        try
        {
            PublishCandidate(candidateRoot, outputRoot);
            var verification = integrityVerifier.VerifyAsync(
                    outputRoot,
                    CancellationToken.None)
                .AsTask()
                .GetAwaiter()
                .GetResult();
            if (!verification.IsValid)
            {
                throw new IOException(
                    "The replacement generated root failed integrity verification.");
            }

            Directory.Delete(transaction, recursive: true);
        }
        catch
        {
            MovePartialIntoTransaction(outputRoot, transaction);
            Directory.Move(backupRoot, outputRoot);
            File.Move(
                backupAnchor,
                GeneratedOutputPathPolicy.AnchorPath(outputRoot));
            throw;
        }
    }

    private static void RepairFromCandidate(
        string candidateRoot,
        string outputRoot,
        string quarantineDigest)
    {
        var parent = Path.GetDirectoryName(outputRoot) ??
            throw new IOException("The generated root has no parent.");
        var rootName = Path.GetFileName(outputRoot);
        var quarantine = Path.Combine(
            parent,
            ".program-kit-quarantine",
            rootName,
            quarantineDigest["sha256:".Length..]);
        if (Directory.Exists(quarantine) || File.Exists(quarantine))
        {
            throw Input(
                "PKREF015",
                "The digest-addressed quarantine destination already exists.",
                "/outputRoot");
        }

        Directory.CreateDirectory(quarantine);
        var quarantinedRoot = Path.Combine(quarantine, "root");
        var quarantinedAnchor = Path.Combine(quarantine, "anchor.json");
        if (Directory.Exists(outputRoot))
        {
            Directory.Move(outputRoot, quarantinedRoot);
        }
        else if (File.Exists(outputRoot))
        {
            File.Move(outputRoot, Path.Combine(quarantine, "root.file"));
        }

        var outputAnchor = GeneratedOutputPathPolicy.AnchorPath(outputRoot);
        if (File.Exists(outputAnchor))
        {
            File.Move(outputAnchor, quarantinedAnchor);
        }

        try
        {
            PublishCandidate(candidateRoot, outputRoot);
        }
        catch
        {
            MovePartialIntoTransaction(outputRoot, quarantine);
            if (Directory.Exists(quarantinedRoot))
            {
                Directory.Move(quarantinedRoot, outputRoot);
            }

            if (File.Exists(quarantinedAnchor))
            {
                File.Move(quarantinedAnchor, outputAnchor);
            }

            throw;
        }
    }

    private static async ValueTask<string> DriftDigestAsync(
        string root,
        GeneratedOutputIntegrityResult result,
        CancellationToken cancellationToken)
    {
        StringBuilder material = new();
        foreach (var issue in result.Issues
                     .OrderBy(static issue => issue.Path, StringComparer.Ordinal)
                     .ThenBy(static issue => issue.Kind))
        {
            material
                .Append("issue|")
                .Append(issue.Kind)
                .Append('|')
                .Append(issue.Path)
                .Append('|')
                .Append(issue.Message)
                .Append('\n');
        }

        if (Directory.Exists(root) &&
            (File.GetAttributes(root) & FileAttributes.ReparsePoint) == 0)
        {
            var pending = new Stack<string>();
            pending.Push(root);
            while (pending.Count > 0)
            {
                cancellationToken.ThrowIfCancellationRequested();
                var directory = pending.Pop();
                foreach (var entry in Directory
                             .EnumerateFileSystemEntries(directory)
                             .Order(StringComparer.Ordinal))
                {
                    var relative = Path
                        .GetRelativePath(root, entry)
                        .Replace('\\', '/');
                    var attributes = File.GetAttributes(entry);
                    material
                        .Append("path|")
                        .Append(relative)
                        .Append('|')
                        .Append((int)attributes)
                        .Append('\n');
                    if ((attributes & FileAttributes.ReparsePoint) != 0)
                    {
                        continue;
                    }

                    if ((attributes & FileAttributes.Directory) != 0)
                    {
                        pending.Push(entry);
                        continue;
                    }

                    await using var stream = File.OpenRead(entry);
                    material
                        .Append("digest|")
                        .Append(relative)
                        .Append("|sha256:")
                        .Append(Convert.ToHexStringLower(
                            await SHA256.HashDataAsync(
                                stream,
                                cancellationToken).ConfigureAwait(false)))
                        .Append('\n');
                }
            }
        }

        var anchor = GeneratedOutputPathPolicy.AnchorPath(root);
        if (File.Exists(anchor) &&
            (File.GetAttributes(anchor) & FileAttributes.ReparsePoint) == 0)
        {
            await using var stream = File.OpenRead(anchor);
            material
                .Append("anchor|sha256:")
                .Append(Convert.ToHexStringLower(
                    await SHA256.HashDataAsync(
                        stream,
                        cancellationToken).ConfigureAwait(false)))
                .Append('\n');
        }

        return string.Concat(
            "sha256:",
            Convert.ToHexStringLower(
                SHA256.HashData(
                    Encoding.UTF8.GetBytes(material.ToString()))));
    }

    private void RecoverCompletedTransaction(string outputRoot)
    {
        var transaction = string.Concat(outputRoot, TransactionSuffix);
        if (!Directory.Exists(transaction))
        {
            return;
        }

        var current = integrityVerifier.VerifyAsync(
                outputRoot,
                CancellationToken.None)
            .AsTask()
            .GetAwaiter()
            .GetResult();
        if (!current.IsValid)
        {
            throw Input(
                "PKREF014",
                "An incomplete refresh transaction was preserved because recovery is ambiguous.",
                "/outputRoot");
        }

        Directory.Delete(transaction, recursive: true);
    }

    private static void MovePartialIntoTransaction(
        string outputRoot,
        string transaction)
    {
        if (Directory.Exists(outputRoot))
        {
            Directory.Move(
                outputRoot,
                Path.Combine(transaction, "failed-root"));
        }

        var anchor = GeneratedOutputPathPolicy.AnchorPath(outputRoot);
        if (File.Exists(anchor))
        {
            File.Move(anchor, Path.Combine(transaction, "failed-anchor.json"));
        }
    }

    private static void DeleteCandidate(string candidateRoot)
    {
        if (Directory.Exists(candidateRoot))
        {
            Directory.Delete(candidateRoot, recursive: true);
        }

        var anchor = GeneratedOutputPathPolicy.AnchorPath(candidateRoot);
        if (File.Exists(anchor))
        {
            File.Delete(anchor);
        }
    }

    private static DotNetHostRefreshException Input(
        string id,
        string message,
        string path) =>
        new(id, CommandExitCode.UsageOrInputFailure, message, path);
}
