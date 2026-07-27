using Orbyss.ProgramKit.Modularity.Ordering;

namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>
/// Non-extendable type-erased view of one explicitly registered typed handler.
/// The internal constructor prevents mutable third-party registration
/// implementations from entering an immutable registry.
/// </summary>
public abstract class DomainContributionHandlerRegistration : IModularityRegistration
{
    internal DomainContributionHandlerRegistration()
    {
    }

    /// <inheritdoc />
    public abstract ModularityRegistrationDescriptor Descriptor { get; }

    /// <summary>Gets the exact contribution type handled by this registration.</summary>
    public abstract Type ContributionType { get; }

    /// <summary>Invokes the typed handler after deterministic registry selection.</summary>
    /// <param name="contribution">The contribution instance.</param>
    /// <param name="cancellationToken">The caller-controlled cancellation token.</param>
    public abstract ValueTask InvokeAsync(
        IDomainContribution contribution,
        CancellationToken cancellationToken);
}
