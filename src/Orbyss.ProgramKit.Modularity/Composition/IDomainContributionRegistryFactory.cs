using Orbyss.ProgramKit.Modularity.Contributions;

namespace Orbyss.ProgramKit.Modularity.Composition;

/// <summary>Creates validated immutable domain-contribution registries.</summary>
public interface IDomainContributionRegistryFactory
{
    /// <summary>Creates a registry from the complete explicit registration set.</summary>
    IDomainContributionRegistry Create(
        IEnumerable<DomainContributionHandlerRegistration> registrations);
}
