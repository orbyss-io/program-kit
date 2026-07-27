namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Exhaustive stable process exit mapping.</summary>
public sealed record OpenConsoleExitCode(
    [property: JsonPropertyName("code")] int Code,
    [property: JsonPropertyName("meaning")] string Meaning,
    [property: JsonPropertyName("diagnosticSchemaRevisions")] ImmutableArray<ArtifactReference> DiagnosticSchemaRevisions);
