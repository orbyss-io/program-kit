namespace Orbyss.ProgramKit.UnitTests.Modularity.Contributions;

internal sealed class DelegateHandler<TContribution> :
    IDomainContributionHandler<TContribution>
    where TContribution : IDomainContribution
{
    private readonly Func<TContribution, CancellationToken, ValueTask> action;

    public DelegateHandler(
        Func<TContribution, CancellationToken, ValueTask> action)
    {
        this.action = action;
    }

    public ValueTask HandleAsync(
        TContribution contribution,
        CancellationToken cancellationToken) =>
        action(contribution, cancellationToken);
}
