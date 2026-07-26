namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>Explicit input for deterministic OpenAPI 3.2.0 projection.</summary>
public sealed record OpenApiDocumentProjection(
    string Title,
    SemanticVersion ApiVersion,
    ImmutableArray<OpenApiServerProjection> Servers,
    ImmutableArray<OpenApiOperationProjection> Operations,
    IntegratorDocumentProvenance Provenance,
    ImmutableArray<OpenApiSecuritySchemeProjection> SecuritySchemes = default);
