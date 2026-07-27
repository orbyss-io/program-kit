namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal sealed class NoOpHandler :
    IDomainContributionHandler<RecordedContribution>
{
    public ValueTask HandleAsync(
        RecordedContribution contribution,
        CancellationToken cancellationToken) =>
        ValueTask.CompletedTask;
}
