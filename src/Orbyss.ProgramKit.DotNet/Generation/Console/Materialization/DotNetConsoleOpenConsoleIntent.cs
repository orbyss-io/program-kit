using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Complete Open Console semantics with only the computed shell revision
/// omitted.
/// </summary>
public sealed record DotNetConsoleOpenConsoleIntent(
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
    ImmutableArray<OpenConsoleCommand> Commands,
    [property: JsonPropertyName("help")] OpenConsoleHelp Help,
    [property: JsonPropertyName("completion")] OpenConsoleCompletion Completion,
    [property: JsonPropertyName("compatibility")]
    ArtifactCompatibility Compatibility,
    [property: JsonPropertyName("generatorRevision")]
    ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("operationRevisions")]
    ImmutableArray<ArtifactReference> OperationRevisions);
