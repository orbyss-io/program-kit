using Orbyss.ProgramKit.Modularity.Contributions;

namespace Orbyss.ProgramKit.Tasks.Observability;

/// <summary>Publishes optional lifecycle observations as domain contributions.</summary>
internal sealed class DomainContributionTaskLifecycleObserver :
    ITaskLifecycleObserver
{
    private readonly IDomainContributionPublisher? publisher;

    internal DomainContributionTaskLifecycleObserver(
        IDomainContributionPublisher? publisher)
    {
        this.publisher = publisher;
    }

    /// <inheritdoc />
    public async ValueTask ObserveAsync(
        TaskLifecycleContribution contribution,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(contribution);
        if (publisher is null)
        {
            return;
        }

        await publisher.PublishAsync(
            contribution,
            DomainContributionPublicationPolicy.Continue,
            cancellationToken).ConfigureAwait(false);
    }
}
