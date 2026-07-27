using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Hash-bound report for one explicitly prepared package.</summary>
public sealed record LocalPackageEntry(
    [property: JsonPropertyName("sourceProjectIdentity")]
    ProgramKitIdentifier SourceProjectIdentity,
    [property: JsonPropertyName("sourceProjectPath")] string SourceProjectPath,
    [property: JsonPropertyName("packageRevision")] ArtifactReference PackageRevision,
    [property: JsonPropertyName("packageId")] string PackageId,
    [property: JsonPropertyName("packageRole")] string PackageRole,
    [property: JsonPropertyName("expectedTarget")] string ExpectedTarget,
    [property: JsonPropertyName("packagePath")] string PackagePath,
    [property: JsonPropertyName("size")] long Size,
    [property: JsonPropertyName("digest")] Sha256Digest Digest,
    [property: JsonPropertyName("nugetContentHash")] string NuGetContentHash,
    [property: JsonPropertyName("dependencies")]
    ImmutableArray<LocalPackageDependency> Dependencies,
    [property: JsonPropertyName("contents")]
    ImmutableArray<LocalPackageContentEntry> Contents);
