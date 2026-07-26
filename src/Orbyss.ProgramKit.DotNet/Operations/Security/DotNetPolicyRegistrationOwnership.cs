namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Ownership of one named ASP.NET Core host policy registration.</summary>
public enum DotNetPolicyRegistrationOwnership
{
    /// <summary>Program Kit registers transport authentication only.</summary>
    ProgramKitAuthenticatedTransport,

    /// <summary>A consumer composition registers the named policy meaning.</summary>
    ExternalConsumer,
}
