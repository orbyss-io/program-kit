using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Open Console semantics selected by the consumer before Program Kit mirrors
/// the selected shell operation-binding schema sets.
/// </summary>
public sealed record DotNetConsoleOpenConsoleSketch(
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
