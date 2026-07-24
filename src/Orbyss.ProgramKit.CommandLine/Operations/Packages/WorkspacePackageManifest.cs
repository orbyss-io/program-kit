using System.Collections.Immutable;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Finite package-preparation input with no solution or directory discovery semantics.</summary>
public sealed record WorkspacePackageManifest(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("sourceRoot")] string SourceRoot,
    [property: JsonPropertyName("packProjectPath")] string PackProjectPath,
    [property: JsonPropertyName("inputVersionMap")] WorkspaceArtifactLocator InputVersionMap,
    [property: JsonPropertyName("inputVersionSelection")]
    WorkspaceArtifactLocator InputVersionSelection,
    [property: JsonPropertyName("packages")] ImmutableArray<WorkspacePackageEntry> Packages,
    [property: JsonPropertyName("externalPackages")]
    ImmutableArray<LockedExternalPackage> ExternalPackages);
