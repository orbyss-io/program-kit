using Orbyss.ProgramKit.Modularity.Contributions;
using ObservatoryScheduling.Core.Contracts.Contributions;

namespace ObservatoryScheduling.Tests.Features;

internal sealed class ViewingScheduledRecorder :
    IDomainContributionHandler<ViewingScheduled>
{
    internal ViewingScheduled? Last { get; private set; }

    public ValueTask HandleAsync(
        ViewingScheduled contribution,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(contribution);
        cancellationToken.ThrowIfCancellationRequested();
        Last = contribution;
        return ValueTask.CompletedTask;
    }
}
