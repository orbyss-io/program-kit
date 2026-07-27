namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal sealed class NoOpInterfaceHandler :
    IDomainContributionHandler<IDomainContribution>
{
    public ValueTask HandleAsync(
        IDomainContribution contribution,
        CancellationToken cancellationToken) =>
        ValueTask.CompletedTask;
}
