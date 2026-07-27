namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Comprehensive deterministic Console integrator document.</summary>
public sealed record OpenConsoleDocument(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("documentVersion")] SemanticVersion DocumentVersion,
    [property: JsonPropertyName("info")] OpenConsoleInfo Info,
    [property: JsonPropertyName("hostRevision")] ArtifactReference HostRevision,
    [property: JsonPropertyName("parsing")] OpenConsoleParsing Parsing,
    [property: JsonPropertyName("globalOptions")] ImmutableArray<OpenConsoleOption> GlobalOptions,
    [property: JsonPropertyName("commands")] ImmutableArray<OpenConsoleCommand> Commands,
    [property: JsonPropertyName("help")] OpenConsoleHelp Help,
    [property: JsonPropertyName("completion")] OpenConsoleCompletion Completion,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility,
    [property: JsonPropertyName("provenance")] OpenConsoleProvenance Provenance);
