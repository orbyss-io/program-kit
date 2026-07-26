namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Finite confidential OIDC client authentication method.</summary>
public enum DotNetOidcClientAuthenticationMethod
{
    /// <summary>Resolve configuration-shaped secret material outside generated input.</summary>
    ClientSecretPost,

    /// <summary>Use a consumer-supplied bounded assertion adapter.</summary>
    PrivateKeyJwtAssertion,
}
