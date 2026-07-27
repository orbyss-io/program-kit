using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal sealed class StubDomainContributionRegistry :
    IDomainContributionRegistry
{
    public ImmutableArray<DomainContributionHandlerRegistration> Registrations =>
        [];

    public ImmutableArray<DomainContributionHandlerRegistration>
        GetRegistrations<TContribution>()
        where TContribution : IDomainContribution =>
        [];

    public ImmutableArray<DomainContributionHandlerRegistration> GetRegistrations(
        Type contributionType) =>
        [];
}
