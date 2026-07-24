namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Exact configuration schema bound to one generated host section.</summary>
public sealed record DotNetConfigurationBinding(
    [property: JsonPropertyName("section")] string Section,
    [property: JsonPropertyName("schemaRevision")] ArtifactReference SchemaRevision,
    [property: JsonPropertyName("required")] bool Required);
