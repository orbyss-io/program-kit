using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Exact-byte local package-root verification with no folder-based selection.</summary>
public sealed class LocalPackageRootVerifier : ILocalPackageRootVerifier
{
    private readonly ICommandFileSystem fileSystem;
    private readonly IProgramKitJsonSerializer serializer;

    /// <summary>Initializes verification with explicit file and JSON mechanics.</summary>
    public LocalPackageRootVerifier(
        ICommandFileSystem fileSystem,
        IProgramKitJsonSerializer serializer)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
    }

    /// <inheritdoc />
    public async ValueTask<VerifiedLocalPackageRoot> VerifyAsync(
        string manifestPath,
        ArtifactReference expectedVersionMap,
        ArtifactReference expectedVersionSelection,
        CancellationToken cancellationToken)
    {
        var fullManifestPath = Path.GetFullPath(manifestPath);
        var root = Path.GetDirectoryName(fullManifestPath) ??
            throw new InvalidDataException(
                "The package-root manifest has no parent directory.");
        var manifestBytes = await fileSystem.ReadAllBytesAsync(
            fullManifestPath,
            cancellationToken).ConfigureAwait(false);
        var manifest = serializer.Read<LocalPackageRootManifest>(
            manifestBytes,
            CommandLineJsonProfiles.LocalOperations.Reference,
            CommandLineJsonProfiles.LocalOperations.MaximumLimits);
        var canonical = serializer.Write(
            manifest,
            CommandLineJsonProfiles.LocalOperations.Reference,
            CommandLineJsonProfiles.LocalOperations.MaximumLimits).ToArray();
        if (!manifestBytes.Span.SequenceEqual(canonical) ||
            !string.Equals(
                manifest.Schema,
                "pkid:schema:program-kit:local-package-root-manifest@1.0.0",
                StringComparison.Ordinal) ||
            manifest.Version != new SemanticVersion("1.0.0") ||
            manifest.Packages.IsDefaultOrEmpty ||
            manifest.ExternalPackages.IsDefault ||
            manifest.InputVersionMap.Revision != expectedVersionMap ||
            manifest.InputVersionSelection.Revision != expectedVersionSelection)
        {
            throw new InvalidDataException(
                "The package-root manifest is noncanonical, incomplete, or bound to different immutable inputs.");
        }

        var selectedPaths = new HashSet<string>(
            OperatingSystem.IsWindows()
                ? StringComparer.OrdinalIgnoreCase
                : StringComparer.Ordinal);
        var packageIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var package in manifest.Packages)
        {
            if (!packageIds.Add(package.PackageId))
            {
                throw new InvalidDataException(
                    "The package-root manifest contains duplicate package IDs.");
            }

            var packagePath = LocalOperationPaths.ResolveBelow(
                root,
                package.PackagePath,
                "A package-root nupkg");
            if (!selectedPaths.Add(packagePath) ||
                !fileSystem.FileExists(packagePath) ||
                fileSystem.GetFileSize(packagePath) != package.Size)
            {
                throw new InvalidDataException(
                    "A selected package path is missing, duplicated, or size-drifted.");
            }

            var packageBytes = await fileSystem.ReadAllBytesAsync(
                packagePath,
                cancellationToken).ConfigureAwait(false);
            if (LocalOperationHashes.Sha256(packageBytes.Span) != package.Digest ||
                !string.Equals(
                    LocalOperationHashes.NuGetContentHash(packageBytes.Span),
                    package.NuGetContentHash,
                    StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    "A selected package does not match its exact content hashes.");
            }
        }

        ValidateExternalPackages(manifest.ExternalPackages, packageIds);
        var unlistedPackages = fileSystem.EnumerateFiles(root)
            .Where(path =>
                path.EndsWith(".nupkg", StringComparison.OrdinalIgnoreCase) &&
                !selectedPaths.Contains(Path.GetFullPath(path)))
            .ToArray();
        if (unlistedPackages.Length != 0)
        {
            throw new InvalidDataException(
                "The package root contains an unlisted nupkg.");
        }

        return new VerifiedLocalPackageRoot(
            root,
            manifest,
            LocalOperationHashes.Sha256(manifestBytes.Span));
    }

    private static void ValidateExternalPackages(
        ImmutableArray<LockedExternalPackage> packages,
        HashSet<string> localPackageIds)
    {
        var externalPackageIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var package in packages)
        {
            if (string.IsNullOrWhiteSpace(package.PackageId) ||
                !externalPackageIds.Add(package.PackageId) ||
                localPackageIds.Contains(package.PackageId) ||
                package.Dependencies.IsDefault)
            {
                throw new InvalidDataException(
                    "External package IDs must be non-empty, unique, and disjoint from local package IDs.");
            }

            var dependencyIds = new HashSet<string>(StringComparer.Ordinal);
            if (package.Dependencies.Any(dependency =>
                    string.IsNullOrWhiteSpace(dependency.PackageId) ||
                    string.IsNullOrWhiteSpace(dependency.VersionRange) ||
                    !dependencyIds.Add(dependency.PackageId)))
            {
                throw new InvalidDataException(
                    "External package dependency edges must be explicit and unique.");
            }
        }

        if (packages.Any(package =>
                package.Dependencies.Any(dependency =>
                    !externalPackageIds.Contains(dependency.PackageId))))
        {
            throw new InvalidDataException(
                "Every external package dependency edge must resolve inside the reviewed closure.");
        }
    }
}
