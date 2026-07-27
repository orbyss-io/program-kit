namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Finite OAuth token types understood by the base service-client profiles.</summary>
public enum DotNetOAuthTokenType
{
    /// <summary>RFC 8693 access-token type.</summary>
    AccessToken,

    /// <summary>RFC 8693 JWT token type.</summary>
    Jwt,
}
