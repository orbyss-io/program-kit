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
        "contentFiles/any/any/.agent-capabilities/capability-bundle-manifest.json";
    private const int MaximumArchiveEntries = 64;
    private const int MaximumManifestBytes = 32 * 1024;
    private const int MaximumPayloadBytes = 512 * 1024;
    private static readonly string[] DistributedCapabilityIds =
    [
        "design-csharp-build-gate",
        "design-software",
        "develop-software",
        "implement-software-plan",
        "maintain-software",
        "publish-dotnet-application-locally",
    ];
    private static readonly string[] RegisteredProviders =
    [
        "claude",
        "codex",
    ];
    private static readonly Dictionary<string, string> SupportingResourcePaths =
        new(StringComparer.Ordinal)
        {
            ["consumer-capability-catalog"] =
                ".agent-capabilities/supporting-resources/catalogs/consumer-capability-catalog-0.1.0-alpha.1.json",
            ["csharp-gate-alpha1-alpha2-migration"] =
                "schemas/csharp-build-gates/csharp-build-gate-definition-alpha.1-to-alpha.2-migration.json",
            ["csharp-gate-authoring-catalog"] =
                ".agent-capabilities/supporting-resources/csharp-gates/csharp-gate-authoring-catalog-0.1.0-alpha.1.json",
            ["dotnet-console-input-materialization-guide"] =
                ".agent-capabilities/supporting-resources/dotnet/dotnet-console-input-materialization-guide.md",
            ["dotnet-console-integration-project-example"] =
                ".agent-capabilities/supporting-resources/dotnet/Example.ConsoleIntegration.csproj",
            ["dotnet-console-integration-source-example"] =
                ".agent-capabilities/supporting-resources/dotnet/ConsoleIntegration.cs",
            ["software-change-completion-profile-set"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/completion-profile-set-1.0.0.json",
            ["software-change-completion-profile-set-schema"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/completion-profile-set-1.0.0.schema.json",
            ["software-change-profile-commit-and-push-coherently"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/commit-and-push-coherently.md",
            ["software-change-profile-publish-with-separate-authority"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/publish-with-separate-authority.md",
            ["software-change-profile-record-evidence-and-review-diff"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/record-evidence-and-review-diff.md",
            ["software-change-profile-refresh-affected-output"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/refresh-affected-output.md",
            ["software-change-profile-review-source"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/review-source.md",
            ["software-change-profile-select-build-and-test"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/select-build-and-test.md",
            ["software-change-profile-verify-integrity"] =
                ".agent-capabilities/supporting-resources/completion-profiles/software-change/profiles/verify-integrity.md",
            ["software-change-troubleshooting"] =
                ".agent-capabilities/supporting-resources/troubleshooting/software-change-troubleshooting.md",
        };
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

        foreach (var resource in manifest.SupportingResources)
        {
            declaredPaths.Add(resource.PackagePath);
            await VerifyPayloadAsync(
                entries,
                resource.PackagePath,
                resource.Sha256,
                cancellationToken).ConfigureAwait(false);
        }

        var actualPayloadPaths = entries.Keys
            .Where(
                path =>
                    path.StartsWith(
                        "contentFiles/any/any/.agent-capabilities/capabilities/",
                        StringComparison.Ordinal) ||
                    path.StartsWith(
                        "contentFiles/any/any/.agent-capabilities/provider-adapters/",
                        StringComparison.Ordinal) ||
                    path.StartsWith(
                        "contentFiles/any/any/.agent-capabilities/supporting-resources/",
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

    internal static void ValidateManifest(CapabilityBundleManifest manifest)
    {
        if (!string.Equals(
                manifest.ManifestVersion,
                "0.1.0-alpha.1",
                StringComparison.Ordinal))
        {
            throw InvalidBundle(
                "The capability bundle manifest format is not supported.",
                "/bundle/manifest/manifestVersion");
        }

        if (!string.Equals(
                manifest.BundleVersion,
                "0.1.0-alpha.2",
                StringComparison.Ordinal) ||
            !string.Equals(
                manifest.KitVersion,
                "0.1.0-alpha.2",
                StringComparison.Ordinal))
        {
            throw InvalidBundle(
                "The bundle and Program Kit versions must match this verifier.",
                "/bundle/manifest/version");
        }

        if (manifest.Capabilities is null ||
            manifest.OptionalProviderAdapters is null ||
            manifest.SupportingResources is null)
        {
            throw InvalidBundle(
                "The bundle manifest arrays must be initialized.",
                "/bundle/manifest");
        }

        ValidateCapabilities(manifest.Capabilities);
        ValidateAdapters(manifest.OptionalProviderAdapters);
        ValidateSupportingResources(manifest.SupportingResources);
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
                "The canonical payload must contain exactly the six consumer capabilities.",
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
                ".agent-capabilities/capabilities/",
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
        var expectedKeys = RegisteredProviders
            .SelectMany(
                provider => DistributedCapabilityIds.Select(
                    capabilityId => string.Concat(
                        provider,
                        "/",
                        capabilityId)))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var actualKeys = adapters
            .Select(
                entry =>
                    entry?.Provider is null || entry.CapabilityId is null
                        ? string.Empty
                        : string.Concat(
                            entry.Provider,
                            "/",
                            entry.CapabilityId))
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!actualKeys.SequenceEqual(expectedKeys, StringComparer.Ordinal))
        {
            throw InvalidBundle(
                "The optional provider-adapter section must contain exactly one adapter per registered provider for each distributable capability.",
                "/bundle/manifest/optionalProviderAdapters");
        }

        foreach (var adapter in adapters)
        {
            var expectedSource = string.Concat(
                ".agent-capabilities/provider-adapters/",
                adapter.Provider,
                "/",
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

    private static void ValidateSupportingResources(
        IReadOnlyCollection<CapabilityBundleSupportingResource> resources)
    {
        var actualIds = resources
            .Select(static entry => entry?.ResourceId)
            .Order(StringComparer.Ordinal)
            .ToArray();
        var expectedIds = SupportingResourcePaths.Keys
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!actualIds.SequenceEqual(expectedIds, StringComparer.Ordinal))
        {
            throw InvalidBundle(
                "The supporting-resource section must contain the exact consumer knowledge resources.",
                "/bundle/manifest/supportingResources");
        }

        foreach (var resource in resources)
        {
            var expectedSource = SupportingResourcePaths[resource.ResourceId];
            var expectedPackage = string.Equals(
                    resource.ResourceId,
                    "csharp-gate-alpha1-alpha2-migration",
                    StringComparison.Ordinal)
                ? "contentFiles/any/any/.agent-capabilities/supporting-resources/csharp-gates/csharp-build-gate-definition-alpha.1-to-alpha.2-migration.json"
                : string.Concat("contentFiles/any/any/", expectedSource);
            ValidatePayloadEntry(
                resource.SourcePath,
                resource.PackagePath,
                resource.Sha256,
                expectedSource,
                expectedPackage,
                "/bundle/manifest/supportingResources");
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
