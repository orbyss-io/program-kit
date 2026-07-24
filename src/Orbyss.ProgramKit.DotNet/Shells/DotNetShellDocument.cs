using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.DotNet.Shells;

/// <summary>Canonical reviewed multi-host .NET shell composition intent.</summary>
public sealed record DotNetShellDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("inputVersionMapRevision")] ArtifactReference InputVersionMapRevision,
    [property: JsonPropertyName("inputVersionSelectionRevision")] ArtifactReference InputVersionSelectionRevision,
    [property: JsonPropertyName("composition")] DotNetShellComposition Composition,
    [property: JsonPropertyName("features")] ImmutableArray<DotNetFeatureSelection> Features,
    [property: JsonPropertyName("jsonSerialization")] DotNetJsonSerializationSelection JsonSerialization,
    [property: JsonPropertyName("hosts")] ImmutableArray<DotNetHostDefinition> Hosts,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility);
