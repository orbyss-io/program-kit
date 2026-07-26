namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Explicit transport intent for an RFC 8693 exchange.</summary>
public enum DotNetOAuthExchangeMode
{
    /// <summary>An actor token is required and remains distinct from the subject.</summary>
    Delegation,

    /// <summary>No actor token is permitted; no domain authority is inferred.</summary>
    Impersonation,
}
