using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Bundles;

/// <summary>Fail-closed verifier for the exact content-only capability package.</summary>
public sealed class CapabilityBundleVerifier : ICapabilityBundleVerifier
{
    private const string ManifestPath =
        "contentFiles/any/any/.program-kit/capability-bundle-manifest.json";
    private const int MaximumArchiveEntries = 64;
    private const int MaximumManifestBytes = 32 * 1024;
    private const int MaximumPayloadBytes = 512 * 1024;
    private static readonly string[] DistributedCapabilityIds =
    [
        "design-software",
        "develop-software",
        "implement-software-plan",
    ];
    private readonly ICapabilityBundleManifestReader manifestReader;

    /// <summary>Initializes the verifier with strict manifest parsing.</summary>
    public CapabilityBundleVerifier(
        ICapabilityBundleManifestReader manifestReader)
    {
        this.manifestReader = manifestReader ??
            throw new ArgumentNullException(nameof(manifestReader));
    }

    /// <inheritdoc />
    public async ValueTask VerifyAsync(
        string bundlePath,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(bundlePath);
        var fullPath = Path.GetFullPath(bundlePath);
        if (!string.Equals(
                Path.GetExtension(fullPath),
                ".nupkg",
                StringComparison.OrdinalIgnoreCase))
        {
            throw InvalidBundle(
                "The capability bundle must be supplied as one .nupkg file.",
                "/bundle");
        }

        try
        {
            await VerifyArchiveAsync(
                fullPath,
                cancellationToken).ConfigureAwait(false);
        }
        catch (CapabilityOperationException)
        {
            throw;
        }
        catch (Exception exception)
            when (exception is IOException or InvalidDataException or
                UnauthorizedAccessException or JsonException)
        {
            throw InvalidBundle(
                "The capability bundle is not a readable strict bundle package.",
                "/bundle");
        }
    }

    private async ValueTask VerifyArchiveAsync(
        string fullPath,
        CancellationToken cancellationToken)
    {
        using var archive = ZipFile.OpenRead(fullPath);
        if (archive.Entries.Count > MaximumArchiveEntries)
        {
            throw InvalidBundle(
                "The capability bundle contains too many archive entries.",
                "/bundle/entries");
        }

        var entries = new Dictionary<string, ZipArchiveEntry>(
            StringComparer.Ordinal);
        foreach (var entry in archive.Entries)
        {
            cancellationToken.ThrowIfCancellationRequested();
            ValidateEntryPath(entry.FullName);
            if (!entries.TryAdd(entry.FullName, entry))
            {
                throw InvalidBundle(
                    $"Archive entry '{entry.FullName}' occurs more than once.",
                    "/bundle/entries");
            }
        }

        if (!entries.TryGetValue(ManifestPath, out var manifestEntry))
        {
            throw InvalidBundle(
                $"The capability bundle is missing '{ManifestPath}'.",
                "/bundle/manifest");
        }

        var manifestBytes = await ReadEntryAsync(
            manifestEntry,
            MaximumManifestBytes,
            cancellationToken).ConfigureAwait(false);
        var manifest = manifestReader.Read(manifestBytes.Span);
        ValidateManifest(manifest);

        var declaredPaths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var capability in manifest.Capabilities)
        {
            declaredPaths.Add(capability.PackagePath);
            await VerifyPayloadAsync(
                entries,
                capability.PackagePath,
                capability.Sha256,
                cancellationToken).ConfigureAwait(false);
        }

        foreach (var adapter in manifest.OptionalProviderAdapters)
        {
            declaredPaths.Add(adapter.PackagePath);
            await VerifyPayloadAsync(
                entries,
                adapter.PackagePath,
                adapter.Sha256,
                cancellationToken).ConfigureAwait(false);
        }

        var actualPayloadPaths = entries.Keys
            .Where(
                path =>
                    path.StartsWith(
                        "contentFiles/any/any/.agents/",
                        StringComparison.Ordinal) ||
                    path.StartsWith(
                        "contentFiles/any/any/.codex/",
                        StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var expectedPayloadPaths = declaredPaths
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!actualPayloadPaths.SequenceEqual(
                expectedPayloadPaths,
                StringComparer.Ordinal))
        {
            throw InvalidBundle(
                "The capability bundle payload differs from its exact manifest allow-list.",
                "/bundle/entries");
        }

        var expectedContentPaths = declaredPaths
            .Append(ManifestPath)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var actualContentPaths = entries.Keys
            .Where(
                path =>
                    path.StartsWith(
                        "contentFiles/any/any/",
                        StringComparison.Ordinal))
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!actualContentPaths.SequenceEqual(
                expectedContentPaths,
                StringComparer.Ordinal))
        {
            throw InvalidBundle(
                "The capability bundle contains undeclared content files.",
                "/bundle/entries");
        }

        if (entries.Keys.Any(IsExecutableOrBuildAsset))
        {
            throw InvalidBundle(
                "The capability bundle contains an executable or build asset.",
                "/bundle/entries");
        }
    }

    private static void ValidateManifest(CapabilityBundleManifest manifest)
    {
        if (!string.Equals(
                manifest.BundleVersion,
                "1.0.0",
                StringComparison.Ordinal) ||
            !string.Equals(
                manifest.KitVersion,
                "0.1.0-alpha.1",
                StringComparison.Ordinal))
        {
            throw InvalidBundle(
                "The bundle and Program Kit versions must match this verifier.",
                "/bundle/manifest/version");
        }

        if (manifest.Capabilities is null ||
            manifest.OptionalProviderAdapters is null)
        {
            throw InvalidBundle(
                "The bundle manifest arrays must be initialized.",
                "/bundle/manifest");
        }

        ValidateCapabilities(manifest.Capabilities);
        ValidateAdapters(manifest.OptionalProviderAdapters);
    }

    private static void ValidateCapabilities(
        IReadOnlyCollection<CapabilityBundlePayloadEntry> capabilities)
    {
        var actualIds = capabilities
            .Select(entry => entry?.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (actualIds.Length != DistributedCapabilityIds.Length ||
            !actualIds.SequenceEqual(
                DistributedCapabilityIds,
                StringComparer.Ordinal))
        {
            throw InvalidBundle(
                "The canonical payload must contain exactly the three distributable development capabilities.",
                "/bundle/manifest/capabilities");
        }

        foreach (var entry in capabilities)
        {
            if (entry is null)
            {
                throw InvalidBundle(
                    "Capability payload entries cannot be null.",
                    "/bundle/manifest/capabilities");
            }

            var expectedSource = string.Concat(
                ".agents/capabilities/",
                entry.CapabilityId,
                "/CAPABILITY.md");
            var expectedPackage = string.Concat(
                "contentFiles/any/any/",
                expectedSource);
            ValidatePayloadEntry(
                entry.SourcePath,
                entry.PackagePath,
                entry.Sha256,
                expectedSource,
                expectedPackage,
                "/bundle/manifest/capabilities");
        }
    }

    private static void ValidateAdapters(
        IReadOnlyCollection<CapabilityBundleProviderAdapter> adapters)
    {
        var actualIds = adapters
            .Select(entry => entry?.CapabilityId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (actualIds.Length != DistributedCapabilityIds.Length ||
            !actualIds.SequenceEqual(
                DistributedCapabilityIds,
                StringComparer.Ordinal))
        {
            throw InvalidBundle(
                "The optional provider-adapter section must contain exactly one adapter for each distributable capability.",
                "/bundle/manifest/optionalProviderAdapters");
        }

        foreach (var adapter in adapters)
        {
            if (adapter is null ||
                !string.Equals(
                    adapter.Provider,
                    "codex",
                    StringComparison.Ordinal))
            {
                throw InvalidBundle(
                    "Every optional adapter must be one explicit Codex wrapper.",
                    "/bundle/manifest/optionalProviderAdapters");
            }

            var expectedSource = string.Concat(
                ".codex/skills/",
                adapter.CapabilityId,
                "/SKILL.md");
            var expectedPackage = string.Concat(
                "contentFiles/any/any/",
                expectedSource);
            ValidatePayloadEntry(
                adapter.SourcePath,
                adapter.PackagePath,
                adapter.Sha256,
                expectedSource,
                expectedPackage,
                "/bundle/manifest/optionalProviderAdapters");
        }
    }

    private static void ValidatePayloadEntry(
        string sourcePath,
        string packagePath,
        string digest,
        string expectedSource,
        string expectedPackage,
        string path)
    {
        if (!string.Equals(sourcePath, expectedSource, StringComparison.Ordinal) ||
            !string.Equals(packagePath, expectedPackage, StringComparison.Ordinal) ||
            !IsSha256(digest))
        {
            throw InvalidBundle(
                "A bundle payload entry has an invalid source path, package path, or SHA-256 digest.",
                path);
        }
    }

    private static async ValueTask VerifyPayloadAsync(
        Dictionary<string, ZipArchiveEntry> entries,
        string packagePath,
        string expectedDigest,
        CancellationToken cancellationToken)
    {
        if (!entries.TryGetValue(packagePath, out var entry))
        {
            throw InvalidBundle(
                $"The declared payload '{packagePath}' is missing.",
                "/bundle/entries");
        }

        var bytes = await ReadEntryAsync(
            entry,
            MaximumPayloadBytes,
            cancellationToken).ConfigureAwait(false);
        var actualDigest = string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(bytes.Span))
                .ToLowerInvariant());
        if (!string.Equals(
                actualDigest,
                expectedDigest,
                StringComparison.Ordinal))
        {
            throw InvalidBundle(
                $"The declared payload '{packagePath}' does not match its SHA-256 digest.",
                "/bundle/entries");
        }
    }

    private static async ValueTask<ReadOnlyMemory<byte>> ReadEntryAsync(
        ZipArchiveEntry entry,
        int maximumBytes,
        CancellationToken cancellationToken)
    {
        if (entry.Length < 0 || entry.Length > maximumBytes)
        {
            throw InvalidBundle(
                $"Archive entry '{entry.FullName}' exceeds its byte limit.",
                "/bundle/entries");
        }

        using var input = entry.Open();
        using var output = new MemoryStream((int)entry.Length);
        await input.CopyToAsync(output, cancellationToken).ConfigureAwait(false);
        if (output.Length != entry.Length)
        {
            throw InvalidBundle(
                $"Archive entry '{entry.FullName}' did not yield its declared byte length.",
                "/bundle/entries");
        }

        return output.ToArray();
    }

    private static void ValidateEntryPath(string path)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            path.Contains('\\') ||
            path.StartsWith('/') ||
            path.Split('/').Any(segment => segment is "." or ".."))
        {
            throw InvalidBundle(
                "The bundle contains an invalid or escaping archive path.",
                "/bundle/entries");
        }
    }

    private static bool IsExecutableOrBuildAsset(string path) =>
        path.EndsWith(".dll", StringComparison.OrdinalIgnoreCase) ||
        path.EndsWith(".exe", StringComparison.OrdinalIgnoreCase) ||
        path.StartsWith("lib/", StringComparison.OrdinalIgnoreCase) ||
        path.StartsWith("ref/", StringComparison.OrdinalIgnoreCase) ||
        path.StartsWith("runtimes/", StringComparison.OrdinalIgnoreCase) ||
        path.StartsWith("tools/", StringComparison.OrdinalIgnoreCase) ||
        path.StartsWith("build/", StringComparison.OrdinalIgnoreCase) ||
        path.StartsWith("buildTransitive/", StringComparison.OrdinalIgnoreCase);

    private static bool IsSha256(string value)
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

    private static CapabilityOperationException InvalidBundle(
        string message,
        string path) =>
        new(
            CommandExitCode.ConformanceFailure,
            CommandDiagnosticIds.InvalidCapabilityBundle,
            path,
            message);
}
