namespace Orbyss.ProgramKit.DotNet.Documentation;

/// <summary>Human-facing identity and version for one generated integrator document.</summary>
public sealed record IntegratorDocumentInfo(
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("summary")] string Summary,
    [property: JsonPropertyName("version")] SemanticVersion Version);
