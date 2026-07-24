namespace Orbyss.ProgramKit.Tasks.Core.Cancellation;

/// <summary>Result of requesting cancellation for accepted work.</summary>
public enum TaskCancellationDisposition
{
    /// <summary>The cancellation request was accepted.</summary>
    Requested,
    /// <summary>Cancellation had already been requested.</summary>
    AlreadyRequested,
    /// <summary>The instance was already terminal.</summary>
    AlreadyTerminal,
    /// <summary>No instance matched the request.</summary>
    UnknownInstance,
    /// <summary>The cancellation request was rejected.</summary>
    Rejected,
}
