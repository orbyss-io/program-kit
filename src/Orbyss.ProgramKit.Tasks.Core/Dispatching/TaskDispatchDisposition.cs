namespace Orbyss.ProgramKit.Tasks.Core.Dispatching;

/// <summary>Acceptance result for bounded background dispatch.</summary>
public enum TaskDispatchDisposition
{
    /// <summary>The request was accepted and an instance was created.</summary>
    Accepted,
    /// <summary>The request was rejected and no instance was created.</summary>
    Rejected,
    /// <summary>Cancellation occurred before the request was accepted.</summary>
    CancelledBeforeAcceptance,
}
