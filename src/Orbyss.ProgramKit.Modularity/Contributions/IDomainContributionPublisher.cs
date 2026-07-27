namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Publishes event-like domain facts to explicitly registered typed handlers.</summary>
public interface IDomainContributionPublisher
{
    /// <summary>Publishes one contribution using explicit failure and cancellation behavior.</summary>
    /// <typeparam name="TContribution">The exact contribution type.</typeparam>
    /// <param name="contribution">The contribution occurrence.</param>
    /// <param name="policy">The explicit publication policy.</param>
    /// <param name="cancellationToken">The caller-controlled cancellation token.</param>
    ValueTask<DomainContributionPublicationResult> PublishAsync<TContribution>(
        TContribution contribution,
        DomainContributionPublicationPolicy policy,
        CancellationToken cancellationToken = default)
        where TContribution : IDomainContribution;
}
