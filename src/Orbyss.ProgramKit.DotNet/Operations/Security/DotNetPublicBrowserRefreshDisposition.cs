namespace Orbyss.ProgramKit.DotNet.Operations.Security;

/// <summary>Explicit public-client refresh-token disposition.</summary>
public enum DotNetPublicBrowserRefreshDisposition
{
    /// <summary>No refresh token or offline-access scope is requested.</summary>
    Absent,

    /// <summary>A provider proves rotation and the adapter keeps it only for the browser session.</summary>
    RotatingBrowserSession,
}
