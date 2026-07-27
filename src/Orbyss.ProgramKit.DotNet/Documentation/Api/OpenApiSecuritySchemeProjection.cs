namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>One exact provider-neutral OpenAPI security-scheme projection.</summary>
public sealed record OpenApiSecuritySchemeProjection(
    string Name,
    OpenApiSecuritySchemeKind Kind,
    Uri? OpenIdConnectUrl,
    string? BearerFormat);
