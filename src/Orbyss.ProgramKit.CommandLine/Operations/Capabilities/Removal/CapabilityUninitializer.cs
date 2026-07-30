using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Contracts.Product;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Removal;

/// <summary>
/// Exact-byte provider removal driven only by workspace ownership evidence.
/// </summary>
public sealed class CapabilityUninitializer : ICapabilityUninitializer
{
    private const string AuthoringWorkspaceMarkerPath =
        ".agent-capabilities/authoring-workspace.json";
    private const string LockPath = ".program-kit/capabilities.lock.json";
    private const int MaximumLockBytes = 256 * 1024;
    private const int MaximumWrapperBytes = 512 * 1024;
    private readonly ICommandFileSystem fileSystem;
    private readonly ICapabilityInitializationLockSerializer lockSerializer;
    private readonly ICapabilityWorkspaceTransaction workspaceTransaction;

    /// <summary>Creates the remover over exact operation boundaries.</summary>
    public CapabilityUninitializer(
        ICommandFileSystem fileSystem,
        ICapabilityInitializationLockSerializer lockSerializer,
        ICapabilityWorkspaceTransaction workspaceTransaction)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.lockSerializer = lockSerializer ??
            throw new ArgumentNullException(nameof(lockSerializer));
        this.workspaceTransaction = workspaceTransaction ??
            throw new ArgumentNullException(nameof(workspaceTransaction));
    }

    /// <inheritdoc />
    public async ValueTask UninitializeAsync(
        string provider,
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        if (!CapabilityProviderContractCatalog.TryGet(provider, out _))
        {
            throw InvalidRemoval(
                "Unsupported provider. Allowed values: claude, codex.",
                "/provider");
        }

        var workspace = FullDirectory(workspaceRoot);
        EnsureNotUserGlobalWorkspace(workspace);
        if (fileSystem.FileExists(
                ResolveUnder(
                    workspace,
                    AuthoringWorkspaceMarkerPath,
                    "/workspaceRoot")))
        {
            throw InvalidRemoval(
                "The Program Kit source authoring workspace rejects consumer capability removal.",
                "/workspaceRoot");
        }

        await workspaceTransaction.RecoverAsync(
            workspace,
            cancellationToken).ConfigureAwait(false);
        var lockFullPath = ResolveUnder(workspace, LockPath, "/lock");
        var ownership = await ReadOwnershipAsync(
            lockFullPath,
            cancellationToken).ConfigureAwait(false);
        var selected = ownership.Providers.SingleOrDefault(
            binding =>
                string.Equals(
                    binding.Provider,
                    provider,
                    StringComparison.Ordinal))
            ?? throw InvalidRemoval(
                "The selected provider is not owned by the Program Kit capability lock.",
                "/provider");

        foreach (var entry in selected.Capabilities)
        {
            var path = ResolveUnder(workspace, entry.OutputPath, "/output");
            var bytes = await ReadBoundedAsync(
                path,
                MaximumWrapperBytes,
                "/output",
                cancellationToken).ConfigureAwait(false);
            if (!string.Equals(
                    Digest(bytes.Span),
                    entry.OutputSha256,
                    StringComparison.Ordinal))
            {
                throw InvalidRemoval(
                    "A selected provider wrapper differs from its exact Program Kit ownership evidence.",
                    "/output");
            }
        }

        var remaining = ownership.Providers
            .Where(
                binding =>
                    !string.Equals(
                        binding.Provider,
                        provider,
                        StringComparison.Ordinal))
            .OrderBy(
                static binding => binding.Provider,
                StringComparer.Ordinal)
            .ToArray();
        ReadOnlyMemory<byte>? desiredLock = null;
        if (remaining.Length != 0)
        {
            if (ownership.Current is null)
            {
                throw InvalidRemoval(
                    "A legacy single-provider lock cannot contain remaining providers.",
                    "/lock");
            }

            desiredLock = lockSerializer.Write(
                ownership.Current with { Providers = remaining });
        }

        var mutations = selected.Capabilities
            .OrderBy(static entry => entry.OutputPath, StringComparer.Ordinal)
            .Select(
                static entry =>
                    new CapabilityWorkspaceMutation(
                        entry.OutputPath,
                        null))
            .Append(
                new CapabilityWorkspaceMutation(
                    LockPath,
                    desiredLock))
            .ToArray();
        await workspaceTransaction.ApplyAsync(
            workspace,
            mutations,
            cancellationToken).ConfigureAwait(false);
    }

    private async ValueTask<RemovalOwnership> ReadOwnershipAsync(
        string path,
        CancellationToken cancellationToken)
    {
        var bytes = await ReadBoundedAsync(
            path,
            MaximumLockBytes,
            "/lock",
            cancellationToken).ConfigureAwait(false);
        try
        {
            var version = lockSerializer.ReadVersion(bytes.Span);
            if (string.Equals(
                    version,
                    ProgramKitProductInfo.CapabilityLockVersion,
                    StringComparison.Ordinal))
            {
                var current = lockSerializer.Read(bytes.Span);
                ValidateCurrent(current);
                return new RemovalOwnership(current, current.Providers);
            }

            var legacy = lockSerializer.ReadLegacy(bytes.Span);
            var provider = ValidateLegacy(legacy);
            return new RemovalOwnership(null, [provider]);
        }
        catch (Exception exception)
            when (exception is JsonException or InvalidOperationException or
                KeyNotFoundException)
        {
            throw InvalidRemoval(
                "The Program Kit capability ownership lock is invalid.",
                "/lock");
        }
    }

    private static void ValidateCurrent(CapabilityInitializationLock value)
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
            throw InvalidRemoval(
                "The Program Kit capability ownership lock is unsupported.",
                "/lock");
        }

        HashSet<string> outputPaths = new(StringComparer.Ordinal);
        foreach (var provider in value.Providers)
        {
            ValidateProvider(provider, outputPaths);
        }
    }

    private static CapabilityInitializationProviderLock ValidateLegacy(
        LegacyCapabilityInitializationLock value)
    {
        if (!string.Equals(value.LockVersion, "1.0.0", StringComparison.Ordinal) ||
            value.Capabilities is null)
        {
            throw InvalidRemoval(
                "The legacy capability ownership lock is unsupported.",
                "/lock");
        }

        var provider = new CapabilityInitializationProviderLock(
            value.Provider,
            value.Capabilities.Select(
                    static entry =>
                        new CapabilityInitializationLockEntry(
                            entry.CapabilityId,
                            entry.CanonicalSha256,
                            entry.AdapterTemplateSha256,
                            entry.OutputPath,
                            entry.OutputSha256))
                .ToArray());
        ValidateProvider(
            provider,
            new HashSet<string>(StringComparer.Ordinal));
        return provider;
    }

    private static void ValidateProvider(
        CapabilityInitializationProviderLock provider,
        HashSet<string> outputPaths)
    {
        if (provider is null ||
            !CapabilityProviderContractCatalog.TryGet(
                provider.Provider,
                out var contract) ||
            provider.Capabilities is null ||
            provider.Capabilities.Length == 0)
        {
            throw InvalidRemoval(
                "The capability ownership lock contains an unsupported provider.",
                "/lock/providers");
        }

        var root = SelectStoredRoot(provider.Capabilities, contract);
        HashSet<string> capabilityIds = new(StringComparer.Ordinal);
        foreach (var entry in provider.Capabilities)
        {
            if (entry is null)
            {
                throw InvalidRemoval(
                    "The capability ownership lock contains invalid wrapper evidence.",
                    "/lock/providers/capabilities");
            }

            var expectedPath = string.Concat(
                root,
                entry.CapabilityId,
                "/SKILL.md");
            if (string.IsNullOrWhiteSpace(entry.CapabilityId) ||
                !capabilityIds.Add(entry.CapabilityId) ||
                !string.Equals(
                    entry.OutputPath,
                    expectedPath,
                    StringComparison.Ordinal) ||
                !outputPaths.Add(entry.OutputPath) ||
                !IsDigest(entry.CanonicalSha256) ||
                !IsDigest(entry.AdapterTemplateSha256) ||
                !IsDigest(entry.OutputSha256))
            {
                throw InvalidRemoval(
                    "The capability ownership lock contains invalid wrapper evidence.",
                    "/lock/providers/capabilities");
            }
        }
    }

    private static string SelectStoredRoot(
        CapabilityInitializationLockEntry[] entries,
        CapabilityProviderContract contract)
    {
        if (entries.All(
                entry =>
                    entry is not null &&
                    entry.OutputPath.StartsWith(
                        contract.ProjectSkillRoot,
                        StringComparison.Ordinal)))
        {
            return contract.ProjectSkillRoot;
        }

        if (contract.LegacyProjectSkillRoot is not null &&
            entries.All(
                entry =>
                    entry is not null &&
                    entry.OutputPath.StartsWith(
                        contract.LegacyProjectSkillRoot,
                        StringComparison.Ordinal)))
        {
            return contract.LegacyProjectSkillRoot;
        }

        throw InvalidRemoval(
            "A provider binding mixes current, legacy, or unsupported output roots.",
            "/lock/providers");
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
            throw InvalidRemoval(
                "A required capability ownership file is missing or exceeds its byte limit.",
                diagnosticPath);
        }

        return await fileSystem.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
    }

    private string FullDirectory(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw InvalidRemoval(
                "An explicit non-empty workspace directory is required.",
                "/workspaceRoot");
        }

        var result = Path.GetFullPath(value);
        if (!fileSystem.DirectoryExists(result))
        {
            throw InvalidRemoval(
                "The explicit workspace directory does not exist.",
                "/workspaceRoot");
        }

        var trimmed = Path.TrimEndingDirectorySeparator(result);
        var filesystemRoot = Path.GetPathRoot(result);
        if (filesystemRoot is not null &&
            string.Equals(
                trimmed,
                Path.TrimEndingDirectorySeparator(filesystemRoot),
                PathComparison()))
        {
            throw InvalidRemoval(
                "A filesystem root cannot be used as a capability workspace.",
                "/workspaceRoot");
        }

        return trimmed;
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
            throw InvalidRemoval(
                "A user-global provider root cannot be used as a capability workspace.",
                "/workspaceRoot");
        }
    }

    private static string ResolveUnder(
        string root,
        string relativePath,
        string diagnosticPath)
    {
        if (string.IsNullOrWhiteSpace(relativePath) ||
            Path.IsPathRooted(relativePath) ||
            relativePath.Contains('\\') ||
            relativePath.Split('/').Any(
                static segment =>
                    string.IsNullOrWhiteSpace(segment) ||
                    segment is "." or ".."))
        {
            throw InvalidRemoval(
                "A capability path is not a safe normalized relative path.",
                diagnosticPath);
        }

        var fullPath = Path.GetFullPath(
            Path.Combine(
                root,
                relativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!fullPath.StartsWith(
                string.Concat(root, Path.DirectorySeparatorChar),
                PathComparison()))
        {
            throw InvalidRemoval(
                "A capability path escapes its explicit workspace.",
                diagnosticPath);
        }

        return fullPath;
    }

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

    private static StringComparison PathComparison() =>
        OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    private static CapabilityOperationException InvalidRemoval(
        string message,
        string path) =>
        new(
            CommandExitCode.ConformanceFailure,
            CommandDiagnosticIds.InvalidCapabilityInitialization,
            path,
            message);

}
