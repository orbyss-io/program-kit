namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Handles one exact domain-contribution type.</summary>
/// <typeparam name="TContribution">The explicitly registered contribution type.</typeparam>
public interface IDomainContributionHandler<in TContribution>
    where TContribution : IDomainContribution
{
    /// <summary>Handles one contribution occurrence.</summary>
    /// <param name="contribution">The event-like fact supplied by domain code.</param>
    /// <param name="cancellationToken">The caller-controlled cancellation token.</param>
    ValueTask HandleAsync(
        TContribution contribution,
        CancellationToken cancellationToken);
}
