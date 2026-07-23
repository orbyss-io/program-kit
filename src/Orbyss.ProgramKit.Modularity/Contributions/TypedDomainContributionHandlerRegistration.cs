using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Modularity.Diagnostics;
using Orbyss.ProgramKit.Modularity.Ordering;

namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Explicitly binds a stable descriptor to one typed contribution handler.</summary>
/// <typeparam name="TContribution">The exact contribution type.</typeparam>
public sealed class TypedDomainContributionHandlerRegistration<TContribution> :
    DomainContributionHandlerRegistration
    where TContribution : IDomainContribution
{
    private readonly IDomainContributionHandler<TContribution> handler;

    /// <summary>Initializes one immutable explicit registration.</summary>
    /// <param name="descriptor">The exact identity, owner, and order.</param>
    /// <param name="handler">The typed handler instance selected by the host.</param>
    public TypedDomainContributionHandlerRegistration(
        ModularityRegistrationDescriptor descriptor,
        IDomainContributionHandler<TContribution> handler)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        ArgumentNullException.ThrowIfNull(handler);
        Descriptor = descriptor;
        this.handler = handler;
    }

    /// <inheritdoc />
    public override ModularityRegistrationDescriptor Descriptor { get; }

    /// <inheritdoc />
    public override Type ContributionType => typeof(TContribution);

    /// <inheritdoc />
    public override ValueTask InvokeAsync(
        IDomainContribution contribution,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(contribution);
        if (contribution is not TContribution typedContribution)
        {
            throw new ModularityValidationException(
                "A contribution registration received an incompatible contribution type.",
                ProgramKitValidationResult.From(
                [
                    ModularityDiagnostics.Error(
                        ModularityDiagnosticIds.ContributionTypeMismatch,
                        string.Concat(
                            "Expected contribution type '",
                            typeof(TContribution).FullName,
                            "' but received '",
                            contribution.GetType().FullName,
                            "'."),
                        "/contribution"),
                ]));
        }

        return handler.HandleAsync(typedContribution, cancellationToken);
    }
}
