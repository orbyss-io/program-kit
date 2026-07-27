namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Exact source revisions from which one console document was authored.</summary>
public sealed record OpenConsoleProvenance(
    [property: JsonPropertyName("shellRevision")] ArtifactReference ShellRevision,
    [property: JsonPropertyName("generatorRevision")] ArtifactReference GeneratorRevision,
    [property: JsonPropertyName("operationRevisions")] ImmutableArray<ArtifactReference> OperationRevisions);
