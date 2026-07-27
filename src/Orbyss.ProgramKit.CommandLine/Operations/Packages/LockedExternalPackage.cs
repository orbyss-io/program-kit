using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>One exact reviewed external restore selection and its locked dependency edges.</summary>
public sealed record LockedExternalPackage(
    [property: JsonPropertyName("packageRevision")] ArtifactReference PackageRevision,
    [property: JsonPropertyName("packageId")] string PackageId,
    [property: JsonPropertyName("contentHash")] string ContentHash,
    [property: JsonPropertyName("dependencies")]
    ImmutableArray<LockedPackageDependency> Dependencies);
