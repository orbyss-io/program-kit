namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Complete parsing and contract descriptor for one option.</summary>
public sealed record OpenConsoleOption(
    [property: JsonPropertyName("longName")] string LongName,
    [property: JsonPropertyName("shortName")] string? ShortName,
    [property: JsonPropertyName("aliases")] ImmutableArray<string> Aliases,
    [property: JsonPropertyName("kind")] ConsoleOptionKind Kind,
    [property: JsonPropertyName("valueType")] string ValueType,
    [property: JsonPropertyName("valueArity")] ConsoleValueArity ValueArity,
    [property: JsonPropertyName("occurrence")] ConsoleOccurrence Occurrence,
    [property: JsonPropertyName("required")] bool Required,
    [property: JsonPropertyName("defaultValue")] string? DefaultValue,
    [property: JsonPropertyName("valueSchemaRevision")] ArtifactReference? ValueSchemaRevision,
    [property: JsonPropertyName("configurationBinding")] string? ConfigurationBinding,
    [property: JsonPropertyName("conflicts")] ImmutableArray<string> Conflicts,
    [property: JsonPropertyName("prerequisites")] ImmutableArray<string> Prerequisites,
    [property: JsonPropertyName("summary")] string Summary);
