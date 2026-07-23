namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Defines explicit per-publication handler failure and cancellation behavior.</summary>
/// <param name="Failure">The handler failure policy.</param>
/// <param name="Cancellation">The handler-thrown cancellation policy.</param>
public sealed record DomainContributionPublicationPolicy(
    DomainContributionFailurePolicy Failure,
    DomainContributionCancellationPolicy Cancellation)
{
    /// <summary>Gets fail-fast publication with propagated cancellation.</summary>
    public static DomainContributionPublicationPolicy FailFast { get; } =
        new(
            DomainContributionFailurePolicy.FailFast,
            DomainContributionCancellationPolicy.Propagate);

    /// <summary>Gets continue-on-failure publication with propagated cancellation.</summary>
    public static DomainContributionPublicationPolicy Continue { get; } =
        new(
            DomainContributionFailurePolicy.Continue,
            DomainContributionCancellationPolicy.Propagate);
}
