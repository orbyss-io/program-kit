namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Complete ordered positional-argument descriptor.</summary>
public sealed record OpenConsoleArgument(
    [property: JsonPropertyName("position")] int Position,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("valueType")] string ValueType,
    [property: JsonPropertyName("valueArity")] ConsoleValueArity ValueArity,
    [property: JsonPropertyName("occurrence")] ConsoleOccurrence Occurrence,
    [property: JsonPropertyName("required")] bool Required,
    [property: JsonPropertyName("defaultValue")] string? DefaultValue,
    [property: JsonPropertyName("valueSchemaRevision")] ArtifactReference ValueSchemaRevision,
    [property: JsonPropertyName("summary")] string Summary);
