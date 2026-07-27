using System.Collections.Immutable;
using System.Text;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Packages;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Fixed non-self-referential local-publish manifest construction.</summary>
internal static class LocalPublishManifestFactory
{
    internal static LocalPublishManifest Create(
        DotNetHostGenerationCommandResult generation,
        VerifiedLocalPackageRoot packageRoot,
        Sha256Digest shellLockDigest,
        ImmutableArray<PublishedApplicationFile> files,
        IProgramKitJsonSerializer serializer)
    {
        ArgumentNullException.ThrowIfNull(generation);
        ArgumentNullException.ThrowIfNull(packageRoot);
        ArgumentNullException.ThrowIfNull(serializer);
        var selectionDigest = PackageSelectionDigest(
            generation,
            packageRoot.Manifest);
        var projection = new LocalPublishManifestDigestProjection(
            "pkid:schema:program-kit:local-publish-manifest@1.0.0",
            new SemanticVersion("1.0.0"),
            generation.Host.Identity,
            generation.Host.Version,
            "GeneratedHost",
            generation.HostLock.Target.SdkVersion,
            generation.HostLock.Target.TargetFramework,
            null,
            "Release",
            "framework-dependent",
            generation.ShellRevision,
            generation.Host.GeneratorProfileRevision,
            generation.Shell.InputVersionMapRevision,
            generation.Shell.InputVersionSelectionRevision,
            shellLockDigest,
            packageRoot.ManifestDigest,
            selectionDigest,
            files,
            new LocalPublishIntegrityProjection("sha256"));
        var projectionBytes = serializer.Write(
            projection,
            CommandLineJsonProfiles.LocalOperations.Reference,
            CommandLineJsonProfiles.LocalOperations.MaximumLimits);
        return new LocalPublishManifest(
            projection.Schema,
            projection.Version,
            projection.HostIdentity,
            projection.HostVersion,
            projection.ProjectName,
            projection.SdkVersion,
            projection.TargetFramework,
            projection.RuntimeIdentifier,
            projection.Configuration,
            projection.DeploymentMode,
            projection.ShellRevision,
            projection.GeneratorRevision,
            projection.InputVersionMapRevision,
            projection.InputVersionSelectionRevision,
            projection.ShellLockDigest,
            projection.PackageRootManifestDigest,
            projection.PackageSelectionDigest,
            projection.Files,
            new ArtifactIntegrity(
                "sha256",
                LocalOperationHashes.Sha256(projectionBytes.ToArray())));
    }

    private static Sha256Digest PackageSelectionDigest(
        DotNetHostGenerationCommandResult generation,
        LocalPackageRootManifest manifest)
    {
        var local = manifest.Packages.ToDictionary(
            static package => package.PackageId,
            StringComparer.Ordinal);
        var external = manifest.ExternalPackages.ToDictionary(
            static package => package.PackageId,
            StringComparer.Ordinal);
        var lines = generation.HostLock.Packages
            .OrderBy(static package => package.PackageId, StringComparer.Ordinal)
            .Select(package =>
            {
                var contentHash = local.TryGetValue(
                    package.PackageId,
                    out var localPackage)
                    ? localPackage.Digest.Value
                    : external.TryGetValue(
                        package.PackageId,
                        out var externalPackage)
                        ? externalPackage.ContentHash
                        : throw new InvalidDataException(
                            "A selected host package is absent from the verified package root.");
                return string.Join(
                    '|',
                    package.PackageId,
                    package.Version.Value,
                    package.PackageDigest.Value,
                    contentHash);
            });
        return LocalOperationHashes.Sha256(
            Encoding.UTF8.GetBytes(string.Join('\n', lines)));
    }
}
