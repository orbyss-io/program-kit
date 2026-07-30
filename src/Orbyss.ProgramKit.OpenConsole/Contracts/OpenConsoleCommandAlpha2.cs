namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>
/// One alpha.2 operation-backed command with explicit schema-set projections.
/// </summary>
public sealed record OpenConsoleCommandAlpha2(
    [property: JsonPropertyName("operationRevision")] ArtifactReference OperationRevision,
    [property: JsonPropertyName("path")] ImmutableArray<string> Path,
    [property: JsonPropertyName("aliases")] ImmutableArray<ImmutableArray<string>> Aliases,
    [property: JsonPropertyName("summary")] string Summary,
    [property: JsonPropertyName("arguments")] ImmutableArray<OpenConsoleArgument> Arguments,
    [property: JsonPropertyName("options")] ImmutableArray<OpenConsoleOption> Options,
    [property: JsonPropertyName("standardInput")] OpenConsoleStreamContract? StandardInput,
    [property: JsonPropertyName("standardOutput")] OpenConsoleStreamContract? StandardOutput,
    [property: JsonPropertyName("standardError")] OpenConsoleStreamContract? StandardError,
    [property: JsonPropertyName("requestSchemaRevisions")]
    ImmutableArray<ArtifactReference> RequestSchemaRevisions,
    [property: JsonPropertyName("resultSchemaRevisions")]
    ImmutableArray<ArtifactReference> ResultSchemaRevisions,
    [property: JsonPropertyName("diagnosticSchemaRevisions")]
    ImmutableArray<ArtifactReference> DiagnosticSchemaRevisions,
    [property: JsonPropertyName("exitCodes")] ImmutableArray<OpenConsoleExitCode> ExitCodes,
    [property: JsonPropertyName("authorityRevision")] ArtifactReference AuthorityRevision,
    [property: JsonPropertyName("examples")] ImmutableArray<OpenConsoleExample> Examples,
    [property: JsonPropertyName("deprecation")] string? Deprecation)
{
    /// <summary>
    /// Projects the exact alpha.2 command into the immutable 1.0.0 reader
    /// shape after alpha.2 validation has completed.
    /// </summary>
    public OpenConsoleCommand ToVersion1() =>
        new(
            OperationRevision,
            Path,
            Aliases,
            Summary,
            Arguments,
            Options,
            StandardInput,
            StandardOutput,
            StandardError,
            ExitCodes,
            AuthorityRevision,
            Examples,
            Deprecation);
}
