using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Canonical exact-byte index for one prepared local package folder.</summary>
public sealed record LocalPackageRootManifest(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("sourceRoot")] string SourceRoot,
    [property: JsonPropertyName("inputVersionMap")] WorkspaceArtifactLocator InputVersionMap,
    [property: JsonPropertyName("inputVersionSelection")]
    WorkspaceArtifactLocator InputVersionSelection,
    [property: JsonPropertyName("packages")] ImmutableArray<LocalPackageEntry> Packages,
    [property: JsonPropertyName("externalPackages")]
    ImmutableArray<LockedExternalPackage> ExternalPackages);
