namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>
/// Current alpha Open Console writer with exact operation schema sets.
/// </summary>
public sealed record OpenConsoleDocumentAlpha2(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("documentVersion")] SemanticVersion DocumentVersion,
    [property: JsonPropertyName("info")] OpenConsoleInfo Info,
    [property: JsonPropertyName("hostRevision")] ArtifactReference HostRevision,
    [property: JsonPropertyName("parsing")] OpenConsoleParsing Parsing,
    [property: JsonPropertyName("hostExitCodeRoles")] OpenConsoleHostExitCodeRoles HostExitCodeRoles,
    [property: JsonPropertyName("globalOptions")] ImmutableArray<OpenConsoleOption> GlobalOptions,
    [property: JsonPropertyName("commands")] ImmutableArray<OpenConsoleCommandAlpha2> Commands,
    [property: JsonPropertyName("help")] OpenConsoleHelp Help,
    [property: JsonPropertyName("completion")] OpenConsoleCompletion Completion,
    [property: JsonPropertyName("compatibility")] ArtifactCompatibility Compatibility,
    [property: JsonPropertyName("provenance")] OpenConsoleProvenance Provenance)
{
    /// <summary>
    /// Projects validated alpha.2 semantics into the immutable 1.0.0 reader
    /// shape used by the existing generator.
    /// </summary>
    public OpenConsoleDocument ToVersion1() =>
        new(
            "pkid:schema:program-kit:open-console@1.0.0",
            new SemanticVersion("1.0.0"),
            Info,
            HostRevision,
            Parsing,
            HostExitCodeRoles,
            GlobalOptions,
            Commands.Select(static command => command.ToVersion1())
                .ToImmutableArray(),
            Help,
            Completion,
            Compatibility,
            Provenance);
}
