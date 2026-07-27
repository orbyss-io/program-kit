namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Explicit non-ambient provenance for a subject or actor token.</summary>
public sealed record DotNetOAuthTokenSource(
    [property: JsonPropertyName("sourceIdentity")] ProgramKitIdentifier SourceIdentity,
    [property: JsonPropertyName("provenanceRevision")] ArtifactReference ProvenanceRevision,
    [property: JsonPropertyName("tokenType")] DotNetOAuthTokenType TokenType);
