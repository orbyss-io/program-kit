using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Complete current-alpha Open Console semantics with only the computed shell
/// revision omitted.
/// </summary>
public sealed record DotNetConsoleOpenConsoleIntentAlpha2(
    [property: JsonPropertyName("$schema")] string Schema,
    [property: JsonPropertyName("documentVersion")]
    SemanticVersion DocumentVersion,
    [property: JsonPropertyName("info")] OpenConsoleInfo Info,
    [property: JsonPropertyName("hostRevision")]
    ArtifactReference HostRevision,
    [property: JsonPropertyName("parsing")] OpenConsoleParsing Parsing,
    [property: JsonPropertyName("hostExitCodeRoles")]
    OpenConsoleHostExitCodeRoles HostExitCodeRoles,
    [property: JsonPropertyName("globalOptions")]
    ImmutableArray<OpenConsoleOption> GlobalOptions,
    [property: JsonPropertyName("commands")]
    ImmutableArray<OpenConsoleCommandAlpha2> Commands,
    [property: JsonPropertyName("help")] OpenConsoleHelp Help,
    [property: JsonPropertyName("completion")] OpenConsoleCompletion Completion,
    [property: JsonPropertyName("compatibility")]
    ArtifactCompatibility Compatibility,
    [property: JsonPropertyName("generatorRevision")]
    ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("operationRevisions")]
    ImmutableArray<ArtifactReference> OperationRevisions)
{
    /// <summary>Projects validated alpha.2 semantics for the legacy generator.</summary>
    public DotNetConsoleOpenConsoleIntent ToVersion1() =>
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
            GeneratorRevision,
            OperationRevisions);
}
