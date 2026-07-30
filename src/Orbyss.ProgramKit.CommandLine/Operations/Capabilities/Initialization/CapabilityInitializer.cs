using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Contracts.Product;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>
/// Transactionally installs exact thin wrappers from this CLI's verified
/// embedded payload and records simultaneous provider ownership.
/// </summary>
public sealed class CapabilityInitializer : ICapabilityInitializer
{
    private const string AuthoringWorkspaceMarkerPath =
        ".agent-capabilities/authoring-workspace.json";
    private const string LockPath = ".program-kit/capabilities.lock.json";
    private const int MaximumWrapperBytes = 512 * 1024;
    private const int MaximumLockBytes = 256 * 1024;
    private readonly ICommandFileSystem fileSystem;
    private readonly IConsumerCapabilityPayload payload;
    private readonly ICapabilityInitializationLockSerializer lockSerializer;
    private readonly ICapabilityWorkspaceTransaction workspaceTransaction;

    /// <summary>Initializes the operation with explicit product boundaries.</summary>
    public CapabilityInitializer(
        ICommandFileSystem fileSystem,
        IConsumerCapabilityPayload payload,
        ICapabilityInitializationLockSerializer lockSerializer,
        ICapabilityWorkspaceTransaction workspaceTransaction)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.payload = payload ??
            throw new ArgumentNullException(nameof(payload));
        this.lockSerializer = lockSerializer ??
            throw new ArgumentNullException(nameof(lockSerializer));
        this.workspaceTransaction = workspaceTransaction ??
            throw new ArgumentNullException(nameof(workspaceTransaction));
    }

    /// <inheritdoc />
    public async ValueTask<CapabilityInitializationResult> InitializeAsync(
        string provider,
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        if (!CapabilityProviderContractCatalog.TryGet(provider, out _))
        {
            throw InvalidInitialization(
                "Unsupported provider. Allowed values: claude, codex.",
                "/provider");
        }

        var workspace = FullDirectory(workspaceRoot, "/workspaceRoot");
        EnsureNotUserGlobalWorkspace(workspace);
        if (fileSystem.FileExists(
                ResolveUnder(
                    workspace,
                    AuthoringWorkspaceMarkerPath,
                    "/workspaceRoot")))
        {
            throw InvalidInitialization(
                "The Program Kit source authoring workspace rejects consumer capability initialization.",
                "/workspaceRoot");
        }

        await workspaceTransaction.RecoverAsync(
            workspace,
            cancellationToken).ConfigureAwait(false);

        var previous = await ReadPreviousStateAsync(
            workspace,
            cancellationToken).ConfigureAwait(false);
        var providers = previous.ProviderNames
            .Append(provider)
            .Distinct(StringComparer.Ordinal)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var candidates = BuildCandidates(workspace, providers);
        var statuses = new Dictionary<string, CandidateStatus>(
            StringComparer.Ordinal);
        foreach (var candidate in candidates)
        {
            statuses.Add(
                candidate.OutputRelativePath,
                await VerifyCollisionAsync(
                    candidate,
                    previous,
                    cancellationToken).ConfigureAwait(false));
        }

        var outputLock = CreateLock(providers, candidates);
        var lockBytes = lockSerializer.Write(outputLock);
        var legacyRemovals = await VerifyLegacyRemovalsAsync(
            workspace,
            previous,
            cancellationToken).ConfigureAwait(false);
        var mutations = candidates
            .Where(
                candidate =>
                    statuses[candidate.OutputRelativePath] !=
                    CandidateStatus.Unchanged)
            .Select(
                static candidate =>
                    new CapabilityWorkspaceMutation(
                        candidate.OutputRelativePath,
                        candidate.OutputBytes))
            .Concat(
                legacyRemovals.Select(
                    static relativePath =>
                        new CapabilityWorkspaceMutation(
                            relativePath,
                            null)))
            .Append(
                new CapabilityWorkspaceMutation(
                    LockPath,
                    lockBytes))
            .ToArray();
        await workspaceTransaction.ApplyAsync(
            workspace,
            mutations,
            cancellationToken).ConfigureAwait(false);
        return new CapabilityInitializationResult(
            provider,
            statuses.Values.Count(static status => status == CandidateStatus.Created),
            statuses.Values.Count(static status => status == CandidateStatus.Updated),
            statuses.Values.Count(static status => status == CandidateStatus.Unchanged),
            LockPath);
    }

    private List<WrapperCandidate> BuildCandidates(
        string workspace,
        IReadOnlyCollection<string> providers)
    {
        List<WrapperCandidate> candidates = [];
        foreach (var provider in providers.Order(StringComparer.Ordinal))
        {
            if (!CapabilityProviderContractCatalog.TryGet(
                    provider,
                    out var contract))
            {
                throw InvalidInitialization(
                    "The provider set contains an unsupported provider.",
                    "/provider");
            }

            var providerRoot = contract.ProjectSkillRoot;
            foreach (var capability in payload.Manifest.Capabilities
                         .OrderBy(
                             static item => item.CapabilityId,
                             StringComparer.Ordinal))
            {
                var adapter = payload.Manifest.OptionalProviderAdapters.Single(
                    item =>
                        string.Equals(
                            item.Provider,
                            provider,
                            StringComparison.Ordinal) &&
                        string.Equals(
                            item.CapabilityId,
                            capability.CapabilityId,
                            StringComparison.Ordinal));
                var outputRelativePath = string.Concat(
                    providerRoot,
                    capability.CapabilityId,
                    "/SKILL.md");
                var outputBytes = payload.ReadAdapter(
                        provider,
                        capability.CapabilityId)
                    .ToArray();
                candidates.Add(
                    new WrapperCandidate(
                        provider,
                        capability.CapabilityId,
                        capability.Sha256,
                        adapter.Sha256,
                        outputRelativePath,
                        ResolveUnder(workspace, outputRelativePath, "/output"),
                        outputBytes,
                        Digest(outputBytes)));
            }
        }

        return candidates;
    }

    private CapabilityInitializationLock CreateLock(
        IEnumerable<string> providers,
        IReadOnlyCollection<WrapperCandidate> candidates) =>
        new(
            ProgramKitProductInfo.CapabilityLockVersion,
            ProgramKitProductInfo.Version,
            payload.Manifest.BundleVersion,
            payload.Manifest.ManifestVersion,
            payload.ManifestSha256,
            providers.Order(StringComparer.Ordinal)
                .Select(
                    provider =>
                        new CapabilityInitializationProviderLock(
                            provider,
                            candidates.Where(
                                    candidate => string.Equals(
                                        candidate.Provider,
                                        provider,
                                        StringComparison.Ordinal))
                                .OrderBy(
                                    static candidate => candidate.CapabilityId,
                                    StringComparer.Ordinal)
                                .Select(
                                    static candidate =>
                                        new CapabilityInitializationLockEntry(
                                            candidate.CapabilityId,
                                            candidate.CanonicalSha256,
                                            candidate.AdapterTemplateSha256,
                                            candidate.OutputRelativePath,
                                            candidate.OutputSha256))
                                .ToArray()))
                .ToArray(),
            payload.Manifest.SupportingResources
                .OrderBy(static item => item.ResourceId, StringComparer.Ordinal)
                .Select(
                    static item =>
                        new CapabilityInitializationResourceLock(
                            item.ResourceId,
                            item.Sha256))
                .ToArray());

    private async ValueTask<CandidateStatus> VerifyCollisionAsync(
        WrapperCandidate candidate,
        PreviousState previous,
        CancellationToken cancellationToken)
    {
        if (!fileSystem.FileExists(candidate.OutputFullPath))
        {
            return CandidateStatus.Created;
        }

        var existing = await ReadBoundedAsync(
            candidate.OutputFullPath,
            MaximumWrapperBytes,
            "/output",
            cancellationToken).ConfigureAwait(false);
        var existingDigest = Digest(existing.Span);
        if (string.Equals(
                existingDigest,
                candidate.OutputSha256,
                StringComparison.Ordinal))
        {
            return CandidateStatus.Unchanged;
        }

        var ownedDigest = previous.OutputDigests.GetValueOrDefault(
            candidate.OutputRelativePath);
        if (ownedDigest is null ||
            !string.Equals(ownedDigest, existingDigest, StringComparison.Ordinal))
        {
            throw InvalidInitialization(
                string.Concat(
                    "Wrapper '",
                    candidate.OutputRelativePath,
                    "' is human-modified or unowned at its current bytes. Program Kit refused every write."),
                "/output");
        }

        return CandidateStatus.Updated;
    }

    private async ValueTask<string[]> VerifyLegacyRemovalsAsync(
        string workspace,
        PreviousState previous,
        CancellationToken cancellationToken)
    {
        foreach (var relativePath in previous.LegacyOutputPaths)
        {
            var path = ResolveUnder(workspace, relativePath, "/output");
            var content = await ReadBoundedAsync(
                path,
                MaximumWrapperBytes,
                "/output",
                cancellationToken).ConfigureAwait(false);
            if (!string.Equals(
                    Digest(content.Span),
                    previous.OutputDigests[relativePath],
                    StringComparison.Ordinal))
            {
                throw InvalidInitialization(
                    string.Concat(
                        "Legacy wrapper '",
                        relativePath,
                        "' no longer matches exact Program Kit ownership evidence."),
                    "/output");
            }
        }

        return previous.LegacyOutputPaths;
    }

    private async ValueTask<PreviousState> ReadPreviousStateAsync(
        string workspace,
        CancellationToken cancellationToken)
    {
        var path = ResolveUnder(workspace, LockPath, "/lock");
        if (!fileSystem.FileExists(path))
        {
            return PreviousState.Empty;
        }

        var bytes = await ReadBoundedAsync(
            path,
            MaximumLockBytes,
            "/lock",
            cancellationToken).ConfigureAwait(false);
        string? lockVersion;
        try
        {
            lockVersion = lockSerializer.ReadVersion(bytes.Span);
        }
        catch (Exception exception)
            when (exception is JsonException or InvalidOperationException or
                KeyNotFoundException)
        {
            throw InvalidInitialization(
                "The existing Program Kit capability lock is not valid JSON ownership evidence.",
                "/lock");
        }

        try
        {
            return string.Equals(
                    lockVersion,
                    ProgramKitProductInfo.CapabilityLockVersion,
                    StringComparison.Ordinal)
                ? ValidateCurrent(lockSerializer.Read(bytes.Span))
                : ValidateLegacy(lockSerializer.ReadLegacy(bytes.Span));
        }
        catch (JsonException)
        {
            throw InvalidInitialization(
                "The existing Program Kit capability lock has an unsupported shape.",
                "/lock");
        }
    }

    private static PreviousState ValidateCurrent(
        CapabilityInitializationLock value)
    {
        if (!string.Equals(
                value.LockVersion,
                ProgramKitProductInfo.CapabilityLockVersion,
                StringComparison.Ordinal) ||
            value.Providers is null ||
            value.Resources is null ||
            value.Providers.Length == 0 ||
            value.Providers.GroupBy(
                    static item => item.Provider,
                    StringComparer.Ordinal)
                .Any(static group => group.Count() != 1))
        {
            throw InvalidInitialization(
                "The existing multi-provider lock is unsupported.",
                "/lock");
        }

        Dictionary<string, string> outputs = new(StringComparer.Ordinal);
        List<string> legacyOutputs = [];
        foreach (var provider in value.Providers)
        {
            if (provider is null ||
                !CapabilityProviderContractCatalog.TryGet(
                    provider.Provider,
                    out var contract) ||
                provider.Capabilities is null)
            {
                throw InvalidInitialization(
                    "The existing lock contains an unsupported provider.",
                    "/lock/providers");
            }

            var root = SelectStoredRoot(provider.Capabilities, contract);
            foreach (var entry in provider.Capabilities)
            {
                ValidateEntry(entry, root);
                if (!outputs.TryAdd(entry.OutputPath, entry.OutputSha256))
                {
                    throw InvalidInitialization(
                        "The existing lock contains duplicate output ownership.",
                        "/lock/providers");
                }

                if (contract.LegacyProjectSkillRoot is not null &&
                    string.Equals(
                        root,
                        contract.LegacyProjectSkillRoot,
                        StringComparison.Ordinal))
                {
                    legacyOutputs.Add(entry.OutputPath);
                }
            }
        }

        return new PreviousState(
            value.Providers.Select(static item => item.Provider).ToArray(),
            outputs,
            legacyOutputs.Order(StringComparer.Ordinal).ToArray());
    }

    private static PreviousState ValidateLegacy(
        LegacyCapabilityInitializationLock value)
    {
        if (!string.Equals(value.LockVersion, "1.0.0", StringComparison.Ordinal) ||
            !CapabilityProviderContractCatalog.TryGet(
                value.Provider,
                out var contract) ||
            value.Capabilities is null)
        {
            throw InvalidInitialization(
                "The legacy capability lock is unsupported and cannot migrate.",
                "/lock");
        }

        var root = SelectStoredRoot(
            value.Capabilities.Select(
                    static entry =>
                        new CapabilityInitializationLockEntry(
                            entry.CapabilityId,
                            entry.CanonicalSha256,
                            entry.AdapterTemplateSha256,
                            entry.OutputPath,
                            entry.OutputSha256))
                .ToArray(),
            contract);
        Dictionary<string, string> outputs = new(StringComparer.Ordinal);
        foreach (var entry in value.Capabilities)
        {
            var currentShape = new CapabilityInitializationLockEntry(
                entry.CapabilityId,
                entry.CanonicalSha256,
                entry.AdapterTemplateSha256,
                entry.OutputPath,
                entry.OutputSha256);
            ValidateEntry(currentShape, root);
            if (!outputs.TryAdd(entry.OutputPath, entry.OutputSha256))
            {
                throw InvalidInitialization(
                    "The legacy lock contains duplicate output ownership.",
                    "/lock");
            }
        }

        var legacyOutputs = contract.LegacyProjectSkillRoot is not null &&
            string.Equals(
                root,
                contract.LegacyProjectSkillRoot,
                StringComparison.Ordinal)
                ? outputs.Keys.Order(StringComparer.Ordinal).ToArray()
                : [];
        return new PreviousState(
            [value.Provider],
            outputs,
            legacyOutputs);
    }

    private static string SelectStoredRoot(
        CapabilityInitializationLockEntry[] entries,
        CapabilityProviderContract contract)
    {
        if (entries.Length != 0 &&
            entries.All(
                entry =>
                    entry is not null &&
                    entry.OutputPath.StartsWith(
                        contract.ProjectSkillRoot,
                        StringComparison.Ordinal)))
        {
            return contract.ProjectSkillRoot;
        }

        if (contract.LegacyProjectSkillRoot is not null &&
            entries.Length != 0 &&
            entries.All(
                entry =>
                    entry is not null &&
                    entry.OutputPath.StartsWith(
                        contract.LegacyProjectSkillRoot,
                        StringComparison.Ordinal)))
        {
            return contract.LegacyProjectSkillRoot;
        }

        throw InvalidInitialization(
            "A provider binding mixes current, legacy, or unsupported output roots.",
            "/lock/providers");
    }

    private static void ValidateEntry(
        CapabilityInitializationLockEntry entry,
        string providerRoot)
    {
        if (entry is null)
        {
            throw InvalidInitialization(
                "A lock wrapper entry is invalid.",
                "/lock/providers/capabilities");
        }

        var expectedPath = string.Concat(
            providerRoot,
            entry.CapabilityId,
            "/SKILL.md");
        if (string.IsNullOrWhiteSpace(entry.CapabilityId) ||
            !string.Equals(
                entry.OutputPath,
                expectedPath,
                StringComparison.Ordinal) ||
            !IsDigest(entry.CanonicalSha256) ||
            !IsDigest(entry.AdapterTemplateSha256) ||
            !IsDigest(entry.OutputSha256))
        {
            throw InvalidInitialization(
                "A lock wrapper entry is invalid.",
                "/lock/providers/capabilities");
        }
    }

    private async ValueTask<ReadOnlyMemory<byte>> ReadBoundedAsync(
        string path,
        int maximumBytes,
        string diagnosticPath,
        CancellationToken cancellationToken)
    {
        if (!fileSystem.FileExists(path) ||
            fileSystem.GetFileSize(path) > maximumBytes)
        {
            throw InvalidInitialization(
                "A required capability file is missing or exceeds its byte limit.",
                diagnosticPath);
        }

        return await fileSystem.ReadAllBytesAsync(path, cancellationToken)
            .ConfigureAwait(false);
    }

    private string FullDirectory(string value, string diagnosticPath)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw InvalidInitialization(
                "An explicit non-empty workspace directory is required.",
                diagnosticPath);
        }

        var result = Path.TrimEndingDirectorySeparator(Path.GetFullPath(value));
        if (!fileSystem.DirectoryExists(result))
        {
            throw InvalidInitialization(
                "The explicit workspace directory does not exist.",
                diagnosticPath);
        }

        var root = Path.GetPathRoot(result);
        if (root is not null &&
            string.Equals(
                result,
                Path.TrimEndingDirectorySeparator(root),
                PathComparison()))
        {
            throw InvalidInitialization(
                "A filesystem root cannot be used as a capability workspace.",
                diagnosticPath);
        }

        return result;
    }

    private static void EnsureNotUserGlobalWorkspace(string workspace)
    {
        var userProfile = Environment.GetFolderPath(
            Environment.SpecialFolder.UserProfile);
        if (!string.IsNullOrWhiteSpace(userProfile) &&
            string.Equals(
                workspace,
                Path.TrimEndingDirectorySeparator(
                    Path.GetFullPath(userProfile)),
                PathComparison()))
        {
            throw InvalidInitialization(
                "A user-global provider root cannot be used as a consumer workspace.",
                "/workspaceRoot");
        }
    }

    private static string ResolveUnder(
        string root,
        string relativePath,
        string diagnosticPath)
    {
        if (string.IsNullOrWhiteSpace(relativePath) ||
            Path.IsPathRooted(relativePath))
        {
            throw InvalidInitialization(
                "A safe repository-relative path is required.",
                diagnosticPath);
        }

        var normalized = relativePath.Replace(
            '/',
            Path.DirectorySeparatorChar);
        var full = Path.GetFullPath(Path.Combine(root, normalized));
        if (!full.StartsWith(
                string.Concat(root, Path.DirectorySeparatorChar),
                PathComparison()))
        {
            throw InvalidInitialization(
                "A capability path escapes the selected workspace.",
                diagnosticPath);
        }

        return full;
    }

    private static StringComparison PathComparison() =>
        OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    private static bool IsDigest(string value)
    {
        if (value is null ||
            value.Length != 71 ||
            !value.StartsWith("sha256:", StringComparison.Ordinal))
        {
            return false;
        }

        foreach (var character in value.AsSpan(7))
        {
            if (character is not (>= '0' and <= '9') and
                not (>= 'a' and <= 'f'))
            {
                return false;
            }
        }

        return true;
    }

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());

    private static CapabilityOperationException InvalidInitialization(
        string message,
        string path) =>
        new(
            CommandExitCode.ConformanceFailure,
            CommandDiagnosticIds.InvalidCapabilityInitialization,
            path,
            message);

}
