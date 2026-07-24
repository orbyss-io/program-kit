namespace Orbyss.ProgramKit.DotNet.Documentation.Console;

/// <summary>Typed stdin, stdout, or stderr contract.</summary>
public sealed record OpenConsoleStreamContract(
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("mediaType")] string MediaType,
    [property: JsonPropertyName("schemaRevision")] ArtifactReference SchemaRevision,
    [property: JsonPropertyName("required")] bool Required);
