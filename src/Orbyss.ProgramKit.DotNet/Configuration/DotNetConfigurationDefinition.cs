namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Owner-authored typed configuration definition consumed by deterministic mechanics.</summary>
public sealed record DotNetConfigurationDefinition(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("version")] SemanticVersion Version,
    [property: JsonPropertyName("ownerIdentity")] ProgramKitIdentifier OwnerIdentity,
    [property: JsonPropertyName("ownerKind")] DotNetConfigurationOwnerKind OwnerKind,
    [property: JsonPropertyName("namespace")] string Namespace,
    [property: JsonPropertyName("typeName")] string TypeName,
    [property: JsonPropertyName("section")] string Section,
    [property: JsonPropertyName("schemaRevision")] ArtifactReference SchemaRevision,
    [property: JsonPropertyName("properties")] ImmutableArray<DotNetConfigurationProperty> Properties,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility);
