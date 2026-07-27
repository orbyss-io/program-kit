using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>
/// Deterministically renders thin provider wrappers without copying canonical
/// capability definitions into a human-led workspace.
/// </summary>
public sealed class CapabilityInitializer : ICapabilityInitializer
{
    private const string CanonicalPathToken =
        "{{PROGRAM_KIT_CANONICAL_CAPABILITY_PATH}}";
    private const string SourceManifestPath =
        ".agent-capabilities/capability-bundle-manifest.json";
    private const string LockPath =
        ".program-kit/capabilities.lock.json";
    private const string LockVersion = "1.0.0";
    private const int MaximumSourceBytes = 512 * 1024;
    private const int MaximumLockBytes = 128 * 1024;
    private static readonly string[] DistributedCapabilityIds =
    [
        "design-software",
        "develop-software",
        "implement-software-plan",
    ];
    private static readonly UTF8Encoding StrictUtf8 = new(
        encoderShouldEmitUTF8Identifier: false,
        throwOnInvalidBytes: true);
    private readonly ICommandFileSystem fileSystem;
    private readonly ICapabilityBundleManifestReader manifestReader;
    private readonly ICapabilityInitializationLockSerializer lockSerializer;

    /// <summary>Initializes the operation with explicit filesystem boundaries.</summary>
    public CapabilityInitializer(
        ICommandFileSystem fileSystem,
        ICapabilityBundleManifestReader manifestReader,
        ICapabilityInitializationLockSerializer lockSerializer)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.manifestReader = manifestReader ??
            throw new ArgumentNullException(nameof(manifestReader));
        this.lockSerializer = lockSerializer ??
            throw new ArgumentNullException(nameof(lockSerializer));
    }

    /// <inheritdoc />
    public async ValueTask InitializeAsync(
        string provider,
        string workspaceRoot,
        string programKitRoot,
        CancellationToken cancellationToken)
    {
        if (!string.Equals(provider, "codex", StringComparison.Ordinal))
        {
            throw InvalidInitialization(
                "Only the exact reviewed 'codex' provider adapter is supported.",
                "/provider");
        }

        var workspace = FullDirectory(workspaceRoot, "/workspaceRoot");
        var kit = FullDirectory(programKitRoot, "/programKitRoot");
        EnsureWithinOrEqual(workspace, kit, "/programKitRoot");

        var manifestPath = ResolveUnder(
            kit,
            SourceManifestPath,
            "/manifest");
        var manifestBytes = await ReadBoundedAsync(
            manifestPath,
            MaximumLockBytes,
            "/manifest",
            cancellationToken).ConfigureAwait(false);
        CapabilityBundleManifest manifest;
        try
        {
            manifest = manifestReader.Read(manifestBytes.Span);
            CapabilityBundleVerifier.ValidateManifest(manifest);
        }
        catch (Exception exception)
            when (exception is JsonException or CapabilityOperationException)
        {
            throw InvalidInitialization(
                "The Program Kit capability source manifest is invalid.",
                "/manifest");
        }

        var previous = await ReadPreviousLockAsync(
            workspace,
            cancellationToken).ConfigureAwait(false);
        var candidates = new List<WrapperCandidate>(
            manifest.Capabilities.Length);
        foreach (var capability in manifest.Capabilities
                     .OrderBy(static item => item.CapabilityId, StringComparer.Ordinal))
        {
            cancellationToken.ThrowIfCancellationRequested();
            var adapter = manifest.OptionalProviderAdapters.Single(
                candidate =>
                    string.Equals(
                        candidate.CapabilityId,
                        capability.CapabilityId,
                        StringComparison.Ordinal) &&
                    string.Equals(
                        candidate.Provider,
                        provider,
                        StringComparison.Ordinal));
            var canonicalPath = ResolveUnder(
                kit,
                capability.SourcePath,
                string.Concat(
                    "/capabilities/",
                    capability.CapabilityId,
                    "/canonical"));
            var templatePath = ResolveUnder(
                kit,
                adapter.SourcePath,
                string.Concat(
                    "/capabilities/",
                    capability.CapabilityId,
                    "/adapter"));
            var canonicalBytes = await ReadBoundedAsync(
                canonicalPath,
                MaximumSourceBytes,
                "/capabilities/canonical",
                cancellationToken).ConfigureAwait(false);
            var templateBytes = await ReadBoundedAsync(
                templatePath,
                MaximumSourceBytes,
                "/capabilities/adapter",
                cancellationToken).ConfigureAwait(false);
            RequireDigest(
                canonicalBytes.Span,
                capability.Sha256,
                "/capabilities/canonical");
            RequireDigest(
                templateBytes.Span,
                adapter.Sha256,
                "/capabilities/adapter");

            var template = DecodeTemplate(templateBytes.Span);
            ValidateTemplate(template);
            var outputRelativePath = string.Concat(
                ".codex/skills/",
                capability.CapabilityId,
                "/SKILL.md");
            var outputPath = ResolveUnder(
                workspace,
                outputRelativePath,
                "/output");
            var outputDirectory = Path.GetDirectoryName(outputPath) ??
                throw InvalidInitialization(
                    "The provider output has no parent directory.",
                    "/output");
            var canonicalPointer = PortableRelativePath(
                outputDirectory,
                canonicalPath);
            var outputBytes = StrictUtf8.GetBytes(
                template.Replace(
                    CanonicalPathToken,
                    canonicalPointer,
                    StringComparison.Ordinal));
            candidates.Add(new WrapperCandidate(
                capability.CapabilityId,
                PortableRelativePath(workspace, canonicalPath),
                capability.Sha256,
                adapter.Sha256,
                outputRelativePath,
                outputPath,
                outputBytes,
                Digest(outputBytes)));
        }

        foreach (var candidate in candidates)
        {
            await VerifyCollisionAsync(
                candidate,
                previous,
                cancellationToken).ConfigureAwait(false);
        }

        foreach (var candidate in candidates)
        {
            cancellationToken.ThrowIfCancellationRequested();
            await fileSystem.WriteAllBytesAsync(
                candidate.OutputFullPath,
                candidate.OutputBytes,
                cancellationToken).ConfigureAwait(false);
        }

        var programKitRelativePath = PortableRelativePath(workspace, kit);
        var outputLock = new CapabilityInitializationLock(
            LockVersion,
            manifest.BundleVersion,
            provider,
            programKitRelativePath,
            Digest(manifestBytes.Span),
            candidates.Select(
                    static candidate =>
                        new CapabilityInitializationLockEntry(
                            candidate.CapabilityId,
                            candidate.CanonicalPath,
                            candidate.CanonicalSha256,
                            candidate.AdapterTemplateSha256,
                            candidate.OutputRelativePath,
                            candidate.OutputSha256))
                .ToArray());
        var lockBytes = lockSerializer.Write(outputLock);
        await fileSystem.WriteAllBytesAsync(
            ResolveUnder(workspace, LockPath, "/lock"),
            lockBytes,
            cancellationToken).ConfigureAwait(false);
    }

    private async ValueTask<CapabilityInitializationLock?> ReadPreviousLockAsync(
        string workspace,
        CancellationToken cancellationToken)
    {
        var path = ResolveUnder(workspace, LockPath, "/lock");
        if (!fileSystem.FileExists(path))
        {
            return null;
        }

        var bytes = await ReadBoundedAsync(
            path,
            MaximumLockBytes,
            "/lock",
            cancellationToken).ConfigureAwait(false);
        CapabilityInitializationLock value;
        try
        {
            value = lockSerializer.Read(bytes.Span);
        }
        catch (JsonException)
        {
            throw InvalidInitialization(
                "The existing Program Kit capability ownership lock is invalid.",
                "/lock");
        }

        if (!string.Equals(
                value.LockVersion,
                LockVersion,
                StringComparison.Ordinal) ||
            !string.Equals(
                value.Provider,
                "codex",
                StringComparison.Ordinal) ||
            !string.Equals(
                value.BundleVersion,
                "2.0.0",
                StringComparison.Ordinal) ||
            !IsDigest(value.ManifestSha256) ||
            !IsSafeStoredRelativePath(
                value.ProgramKitRoot,
                allowCurrentDirectory: true) ||
            !HasExactValidLockEntries(value.Capabilities))
        {
            throw InvalidInitialization(
                "The existing Program Kit capability ownership lock is unsupported.",
                "/lock");
        }

        return value;
    }

    private async ValueTask VerifyCollisionAsync(
        WrapperCandidate candidate,
        CapabilityInitializationLock? previous,
        CancellationToken cancellationToken)
    {
        if (!fileSystem.FileExists(candidate.OutputFullPath))
        {
            return;
        }

        var existing = await ReadBoundedAsync(
            candidate.OutputFullPath,
            MaximumSourceBytes,
            "/output",
            cancellationToken).ConfigureAwait(false);
        var existingDigest = Digest(existing.Span);
        if (string.Equals(
                existingDigest,
                candidate.OutputSha256,
                StringComparison.Ordinal))
        {
            return;
        }

        var owned = previous?.Capabilities.SingleOrDefault(
            entry =>
                string.Equals(
                    entry.OutputPath,
                    candidate.OutputRelativePath,
                    StringComparison.Ordinal));
        if (owned is null ||
            !string.Equals(
                owned.OutputSha256,
                existingDigest,
                StringComparison.Ordinal))
        {
            throw InvalidInitialization(
                string.Concat(
                    "The provider wrapper '",
                    candidate.OutputRelativePath,
                    "' differs and is not owned at its current bytes by the Program Kit lock."),
                "/output");
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
                "A required capability initialization file is missing or exceeds its byte limit.",
                diagnosticPath);
        }

        return await fileSystem.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
    }

    private string FullDirectory(string value, string diagnosticPath)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw InvalidInitialization(
                "An explicit non-empty directory is required.",
                diagnosticPath);
        }

        var result = Path.GetFullPath(value);
        if (!fileSystem.DirectoryExists(result))
        {
            throw InvalidInitialization(
                "The explicit directory does not exist.",
                diagnosticPath);
        }

        var trimmed = Path.TrimEndingDirectorySeparator(result);
        var filesystemRoot = Path.GetPathRoot(result);
        if (filesystemRoot is not null &&
            string.Equals(
                trimmed,
                Path.TrimEndingDirectorySeparator(filesystemRoot),
                PathComparison()))
        {
            throw InvalidInitialization(
                "A filesystem root cannot be used as a capability workspace.",
                diagnosticPath);
        }

        return trimmed;
    }

    private static void EnsureWithinOrEqual(
        string root,
        string candidate,
        string diagnosticPath)
    {
        if (string.Equals(root, candidate, PathComparison()) ||
            candidate.StartsWith(
                string.Concat(root, Path.DirectorySeparatorChar),
                PathComparison()))
        {
            return;
        }

        throw InvalidInitialization(
            "Program Kit must be the workspace root or a directory beneath it.",
            diagnosticPath);
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
            throw InvalidInitialization(
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
            throw InvalidInitialization(
                "A capability path escapes its explicit root.",
                diagnosticPath);
        }

        return fullPath;
    }

    private static string DecodeTemplate(ReadOnlySpan<byte> content)
    {
        try
        {
            return StrictUtf8.GetString(content);
        }
        catch (DecoderFallbackException)
        {
            throw InvalidInitialization(
                "The provider adapter template is not strict UTF-8.",
                "/capabilities/adapter");
        }
    }

    private static void ValidateTemplate(string template)
    {
        if (template.Length > 4096 ||
            Count(template, CanonicalPathToken) != 1 ||
            template.Contains("## Procedure", StringComparison.Ordinal) ||
            template.Contains("## Allowed actions", StringComparison.Ordinal) ||
            template.Contains("## Prohibited actions", StringComparison.Ordinal))
        {
            throw InvalidInitialization(
                "The Codex adapter must remain thin and contain exactly one canonical-path token.",
                "/capabilities/adapter");
        }
    }

    private static int Count(string value, string token)
    {
        var count = 0;
        var index = 0;
        while ((index = value.IndexOf(
                   token,
                   index,
                   StringComparison.Ordinal)) >= 0)
        {
            count++;
            index += token.Length;
        }

        return count;
    }

    private static string PortableRelativePath(string start, string target)
    {
        var value = Path.GetRelativePath(start, target).Replace('\\', '/');
        if (Path.IsPathRooted(value) ||
            value.Contains('`') ||
            value.Any(char.IsControl))
        {
            throw InvalidInitialization(
                "The canonical capability cannot be represented by one safe portable relative pointer.",
                "/output");
        }

        return value;
    }

    private static void RequireDigest(
        ReadOnlySpan<byte> content,
        string expected,
        string path)
    {
        if (!string.Equals(Digest(content), expected, StringComparison.Ordinal))
        {
            throw InvalidInitialization(
                "A canonical capability or provider adapter differs from its exact manifest digest.",
                path);
        }
    }

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());

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

    private static bool HasExactValidLockEntries(
        CapabilityInitializationLockEntry[]? entries)
    {
        if (entries is null ||
            entries.Length != DistributedCapabilityIds.Length)
        {
            return false;
        }

        var actualIds = entries
            .Select(static entry => entry?.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!actualIds.SequenceEqual(
                DistributedCapabilityIds,
                StringComparer.Ordinal))
        {
            return false;
        }

        foreach (var entry in entries)
        {
            if (entry is null ||
                !string.Equals(
                    entry.OutputPath,
                    string.Concat(
                        ".codex/skills/",
                        entry.CapabilityId,
                        "/SKILL.md"),
                    StringComparison.Ordinal) ||
                !IsSafeStoredRelativePath(
                    entry.CanonicalPath,
                    allowCurrentDirectory: false) ||
                !IsDigest(entry.CanonicalSha256) ||
                !IsDigest(entry.AdapterTemplateSha256) ||
                !IsDigest(entry.OutputSha256))
            {
                return false;
            }
        }

        return true;
    }

    private static bool IsSafeStoredRelativePath(
        string value,
        bool allowCurrentDirectory)
    {
        if (allowCurrentDirectory &&
            string.Equals(value, ".", StringComparison.Ordinal))
        {
            return true;
        }

        return !string.IsNullOrWhiteSpace(value) &&
            !Path.IsPathRooted(value) &&
            !value.Contains('\\') &&
            !value.Any(char.IsControl) &&
            value.Split('/').All(
                static segment =>
                    !string.IsNullOrWhiteSpace(segment) &&
                    segment is not "." and not "..");
    }

    private static StringComparison PathComparison() =>
        OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    private static CapabilityOperationException InvalidInitialization(
        string message,
        string path) =>
        new(
            CommandExitCode.ConformanceFailure,
            CommandDiagnosticIds.InvalidCapabilityInitialization,
            path,
            message);

}
