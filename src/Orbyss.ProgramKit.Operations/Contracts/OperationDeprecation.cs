namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>Mechanical discovery metadata for a deprecated operation revision.</summary>
public sealed record OperationDeprecation(
    [property: JsonPropertyName("isDeprecated")] bool IsDeprecated,
    [property: JsonPropertyName("replacedBy")] ArtifactReference? ReplacedBy);
