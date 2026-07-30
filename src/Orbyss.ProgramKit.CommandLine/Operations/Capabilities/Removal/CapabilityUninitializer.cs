using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Removal;

/// <summary>
/// Exact-byte provider removal driven only by workspace ownership evidence.
/// </summary>
public sealed class CapabilityUninitializer : ICapabilityUninitializer
{
    private const string LockPath = ".program-kit/capabilities.lock.json";
    private const int MaximumLockBytes = 128 * 1024;
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
                "Only the exact reviewed 'claude' and 'codex' provider adapters are supported.",
                "/provider");
        }

        var workspace = FullDirectory(workspaceRoot);
        EnsureNotUserGlobalWorkspace(workspace);
        await workspaceTransaction.RecoverAsync(
            workspace,
            cancellationToken).ConfigureAwait(false);
        var lockFullPath = ResolveUnder(workspace, LockPath, "/lock");
        var ownership = await ReadLockAsync(
            lockFullPath,
            cancellationToken).ConfigureAwait(false);
        CapabilityInitializationLockVerifier.Verify(ownership);
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
            desiredLock = lockSerializer.Write(
                new CapabilityInitializationLock("2.0.0", remaining));
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

    private async ValueTask<CapabilityInitializationLock> ReadLockAsync(
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
            return lockSerializer.Read(bytes.Span);
        }
        catch (JsonException)
        {
            throw InvalidRemoval(
                "The Program Kit capability ownership lock is invalid.",
                "/lock");
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
