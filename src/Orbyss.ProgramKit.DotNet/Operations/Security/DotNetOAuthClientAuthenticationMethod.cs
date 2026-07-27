namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Finite OAuth service-client authentication method.</summary>
public enum DotNetOAuthClientAuthenticationMethod
{
    /// <summary>HTTP Basic client authentication at the token endpoint.</summary>
    ClientSecretBasic,

    /// <summary>Form-encoded client authentication at the token endpoint.</summary>
    ClientSecretPost,

    /// <summary>Consumer-supplied private-key JWT assertion service.</summary>
    PrivateKeyJwtAssertion,
}
