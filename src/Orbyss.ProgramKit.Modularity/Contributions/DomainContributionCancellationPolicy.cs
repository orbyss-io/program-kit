namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Controls handler-thrown cancellation when the caller token was not canceled.</summary>
public enum DomainContributionCancellationPolicy
{
    /// <summary>Propagate every handler-thrown <see cref="OperationCanceledException"/>.</summary>
    Propagate,

    /// <summary>
    /// Treat cancellation as a handler failure only when the caller token has
    /// not requested cancellation; caller cancellation always propagates.
    /// </summary>
    TreatUnrequestedCancellationAsFailure,
}
