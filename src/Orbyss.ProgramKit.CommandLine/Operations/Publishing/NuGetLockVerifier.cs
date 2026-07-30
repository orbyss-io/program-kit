using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Fail-closed exact package-ID/version/content-hash restore closure verifier.</summary>
public sealed class NuGetLockVerifier : INuGetLockVerifier
{
    private readonly IProgramKitJsonSerializer serializer;

    /// <summary>Initializes lock verification with the fixed typed JSON mechanics.</summary>
    public NuGetLockVerifier(IProgramKitJsonSerializer serializer)
    {
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
    }

    /// <inheritdoc />
    public void Verify(
        ReadOnlyMemory<byte> lockBytes,
        LocalPackageRootManifest packageManifest,
        DotNetHostLock hostLock)
    {
        ArgumentNullException.ThrowIfNull(packageManifest);
        ArgumentNullException.ThrowIfNull(hostLock);
        NuGetLockFile lockFile;
        try
        {
            lockFile = serializer.Read<NuGetLockFile>(
                lockBytes,
                CommandLineJsonProfiles.LocalOperations.Reference,
                CommandLineJsonProfiles.LocalOperations.MaximumLimits);
        }
        catch (ProgramKitJsonException exception)
        {
            throw new NuGetLockReadException(
                string.Concat(
                    "The NuGet lock does not match the supported strict typed shape. ",
                    exception.Message),
                exception.Diagnostic.Path,
                exception);
        }

        if (lockFile.Version != 1 ||
            !lockFile.Dependencies.TryGetValue(
                hostLock.Target.TargetFramework,
                out var libraries) ||
            lockFile.Dependencies.Count != 1)
        {
            throw new InvalidDataException(
                string.Concat(
                    "The NuGet lock must contain exactly one expected target framework. ",
                    "Expected version 1 and target ",
                    hostLock.Target.TargetFramework,
                    "; observed version ",
                    lockFile.Version,
                    " and targets ",
                    string.Join(
                        ", ",
                        lockFile.Dependencies.Keys.Order(StringComparer.Ordinal)),
                    "."));
        }

        var local = packageManifest.Packages.ToDictionary(
            static package => package.PackageId,
            StringComparer.Ordinal);
        var external = packageManifest.ExternalPackages.ToDictionary(
            static package => package.PackageId,
            StringComparer.Ordinal);
        foreach (var item in libraries)
        {
            if (local.TryGetValue(item.Key, out var localPackage))
            {
                RequireExact(
                    item.Key,
                    item.Value,
                    localPackage.PackageRevision.Version.Value,
                    localPackage.NuGetContentHash);
            }
            else if (external.TryGetValue(item.Key, out var externalPackage))
            {
                RequireExact(
                    item.Key,
                    item.Value,
                    externalPackage.PackageRevision.Version.Value,
                    externalPackage.ContentHash);
                RequireDependencies(item.Value, externalPackage);
            }
            else
            {
                throw new InvalidDataException(
                    string.Concat(
                        "The restore selected an unlisted package: ",
                        item.Key));
            }
        }

        foreach (var package in hostLock.Packages)
        {
            if (!libraries.TryGetValue(package.PackageId, out var selected) ||
                !string.Equals(
                    selected.Resolved,
                    package.Version.Value,
                    StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    string.Concat(
                        "The selected host package is absent or version-drifted: ",
                        package.PackageId));
            }

            var revision = local.TryGetValue(package.PackageId, out var localPackage)
                ? localPackage.PackageRevision
                : external.TryGetValue(package.PackageId, out var externalPackage)
                    ? externalPackage.PackageRevision
                    : null;
            if (revision is null ||
                revision.Version != package.Version ||
                revision.Digest != package.PackageDigest)
            {
                throw new InvalidDataException(
                    string.Concat(
                        "The selected host package revision does not match its package-root evidence: ",
                        package.PackageId));
            }
        }
    }

    private static void RequireExact(
        string packageId,
        NuGetLockLibrary selected,
        string version,
        string contentHash)
    {
        if (!string.Equals(selected.Type, "Direct", StringComparison.Ordinal) &&
            !string.Equals(selected.Type, "Transitive", StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                string.Concat(
                    "The lock contains an unsupported package selection type: ",
                    packageId));
        }

        if (!string.Equals(selected.Resolved, version, StringComparison.Ordinal) ||
            !string.Equals(
                selected.ContentHash,
                contentHash,
                StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                string.Concat(
                    "The lock version or content hash drifted for package: ",
                    packageId));
        }
    }

    private static void RequireDependencies(
        NuGetLockLibrary selected,
        LockedExternalPackage expected)
    {
        var actual = selected.Dependencies ??
            System.Collections.Immutable.ImmutableDictionary<string, string>.Empty;
        if (actual.Count != expected.Dependencies.Length)
        {
            throw new InvalidDataException(
                string.Concat(
                    "The external dependency closure drifted for package: ",
                    expected.PackageId));
        }

        foreach (var dependency in expected.Dependencies)
        {
            if (!actual.TryGetValue(dependency.PackageId, out var range) ||
                !string.Equals(
                    range,
                    dependency.VersionRange,
                    StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    string.Concat(
                        "An external dependency edge drifted for package: ",
                        expected.PackageId));
            }
        }
    }
}
