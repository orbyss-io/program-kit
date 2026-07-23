using System.Collections.Immutable;
namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>
/// Immutable registry of explicitly supplied contribution-handler registrations.
/// It performs exact-type lookup only and never scans assemblies or containers.
/// </summary>
public sealed class DomainContributionRegistry : IDomainContributionRegistry
{
    private readonly ImmutableDictionary<Type, ImmutableArray<DomainContributionHandlerRegistration>>
        registrationsByType;

    internal DomainContributionRegistry(
        ImmutableArray<DomainContributionHandlerRegistration> registrations,
        ImmutableDictionary<Type, ImmutableArray<DomainContributionHandlerRegistration>>
            registrationsByType)
    {
        Registrations = registrations;
        this.registrationsByType = registrationsByType;
    }

    /// <summary>Gets all registrations ordered by stable identity for catalog projection.</summary>
    public ImmutableArray<DomainContributionHandlerRegistration> Registrations { get; }

    /// <summary>Gets handlers for the exact contribution type in execution order.</summary>
    /// <typeparam name="TContribution">The exact contribution type.</typeparam>
    public ImmutableArray<DomainContributionHandlerRegistration>
        GetRegistrations<TContribution>()
        where TContribution : IDomainContribution =>
        GetRegistrations(typeof(TContribution));

    /// <summary>Gets handlers for the exact supplied contribution type in execution order.</summary>
    /// <param name="contributionType">The exact contribution type.</param>
    public ImmutableArray<DomainContributionHandlerRegistration> GetRegistrations(
        Type contributionType)
    {
        ArgumentNullException.ThrowIfNull(contributionType);
        return registrationsByType.TryGetValue(contributionType, out var registrations)
            ? registrations
            : [];
    }
}
