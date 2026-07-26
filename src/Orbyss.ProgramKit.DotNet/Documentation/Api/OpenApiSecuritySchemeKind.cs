namespace Orbyss.ProgramKit.DotNet.Documentation.Api;

/// <summary>Finite provider-neutral OpenAPI authentication scheme kind.</summary>
public enum OpenApiSecuritySchemeKind
{
    /// <summary>OpenID Connect discovery metadata.</summary>
    OpenIdConnect,

    /// <summary>OAuth access token carried by HTTP Bearer authentication.</summary>
    HttpBearerJwt,
}
