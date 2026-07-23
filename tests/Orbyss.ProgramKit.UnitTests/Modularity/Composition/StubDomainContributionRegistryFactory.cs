namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal sealed class StubDomainContributionRegistryFactory :
    IDomainContributionRegistryFactory
{
    private readonly IDomainContributionRegistry registry;

    internal StubDomainContributionRegistryFactory(
        IDomainContributionRegistry registry)
    {
        this.registry = registry;
    }

    public IDomainContributionRegistry Create(
        IEnumerable<DomainContributionHandlerRegistration> registrations) =>
        registry;
}
