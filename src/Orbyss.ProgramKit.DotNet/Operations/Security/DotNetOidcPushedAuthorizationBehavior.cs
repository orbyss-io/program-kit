namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Exact RFC 9126 pushed-authorization disposition.</summary>
public enum DotNetOidcPushedAuthorizationBehavior
{
    /// <summary>Require advertised PAR support.</summary>
    Require,

    /// <summary>Use PAR only when provider metadata advertises support.</summary>
    UseIfAvailable,

    /// <summary>Disable PAR for a provider profile that does not support it.</summary>
    Disable,
}
