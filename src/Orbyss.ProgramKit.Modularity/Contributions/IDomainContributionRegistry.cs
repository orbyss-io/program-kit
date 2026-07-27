using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Provides immutable exact-type contribution-handler registrations.</summary>
public interface IDomainContributionRegistry
{
    /// <summary>Gets all registrations in stable catalog order.</summary>
    ImmutableArray<DomainContributionHandlerRegistration> Registrations { get; }

    /// <summary>Gets handlers for the exact generic contribution type.</summary>
    ImmutableArray<DomainContributionHandlerRegistration>
        GetRegistrations<TContribution>()
        where TContribution : IDomainContribution;

    /// <summary>Gets handlers for the exact supplied contribution type.</summary>
    ImmutableArray<DomainContributionHandlerRegistration> GetRegistrations(
        Type contributionType);
}
