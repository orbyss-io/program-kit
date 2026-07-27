namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Language-neutral human-facing identity of one console document.</summary>
public sealed record OpenConsoleInfo(
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("summary")] string Summary,
    [property: JsonPropertyName("version")] SemanticVersion Version);
