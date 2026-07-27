namespace Orbyss.ProgramKit.DotNet.Documentation.Console;

/// <summary>One operation-backed command descriptor shared by docs and parser generation.</summary>
public sealed record OpenConsoleCommand(
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("path")] ImmutableArray<string> Path,
    [property: JsonPropertyName("aliases")] ImmutableArray<ImmutableArray<string>> Aliases,
    [property: JsonPropertyName("summary")] string Summary,
    [property: JsonPropertyName("arguments")] ImmutableArray<OpenConsoleArgument> Arguments,
    [property: JsonPropertyName("options")] ImmutableArray<OpenConsoleOption> Options,
    [property: JsonPropertyName("standardInput")] OpenConsoleStreamContract? StandardInput,
    [property: JsonPropertyName("standardOutput")] OpenConsoleStreamContract? StandardOutput,
    [property: JsonPropertyName("standardError")] OpenConsoleStreamContract? StandardError,
    [property: JsonPropertyName("exitCodes")] ImmutableArray<OpenConsoleExitCode> ExitCodes,
    [property: JsonPropertyName("authorityRevision")] ArtifactReference AuthorityRevision,
    [property: JsonPropertyName("examples")] ImmutableArray<OpenConsoleExample> Examples,
    [property: JsonPropertyName("deprecation")] string? Deprecation);
