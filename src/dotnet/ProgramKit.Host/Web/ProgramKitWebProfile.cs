namespace ProgramKit.Host.Web;

/// <summary>Identifies the host's versioned browser authentication shape.</summary>
internal enum ProgramKitWebProfile
{
    /// <summary>Disables the authenticated web boundary for non-web workloads.</summary>
    None,

    /// <summary>Uses a same-origin BFF with server-held tokens and an encrypted session cookie.</summary>
    BffCookie,

    /// <summary>Accepts bearer tokens from an explicitly selected direct PKCE browser client.</summary>
    SpaPkce
}
