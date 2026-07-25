namespace Orbyss.ProgramKit.DotNet.Operations.TransportFailures;

/// <summary>Behavior when response headers were already sent.</summary>
public enum DotNetResponseStartedDisposition
{
    /// <summary>Do not rewrite the response and leave the exception unhandled.</summary>
    LeaveUnhandled,
}
