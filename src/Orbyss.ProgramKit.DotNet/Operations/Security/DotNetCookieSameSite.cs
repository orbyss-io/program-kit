namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Finite SameSite selection for generated security cookies.</summary>
public enum DotNetCookieSameSite
{
    /// <summary>SameSite Lax.</summary>
    Lax,

    /// <summary>SameSite None with mandatory secure transport.</summary>
    None,
}
