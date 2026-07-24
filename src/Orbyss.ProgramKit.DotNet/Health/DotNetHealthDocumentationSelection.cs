namespace Orbyss.ProgramKit.DotNet.Health;

/// <summary>Explicit health documentation decision and optional operation.</summary>
public sealed record DotNetHealthDocumentationSelection(
    [property: JsonPropertyName("disposition")] DotNetHealthDocumentationDisposition Disposition,
    [property: JsonPropertyName("operationRevision")] ArtifactReference? OperationRevision);
