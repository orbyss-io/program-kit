using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Modularity.Contributions;
using Orbyss.ProgramKit.Modularity.Diagnostics;
using Orbyss.ProgramKit.Modularity.Ordering;

namespace Orbyss.ProgramKit.Modularity.Composition;

/// <summary>Default validated domain-contribution registry factory.</summary>
public sealed class DomainContributionRegistryFactory :
    IDomainContributionRegistryFactory
{
    private readonly IProgramKitSemanticValidator<ArtifactReference>
        artifactReferenceValidator;

    /// <summary>Initializes the factory with its semantic reference validator.</summary>
    public DomainContributionRegistryFactory(
        IProgramKitSemanticValidator<ArtifactReference> artifactReferenceValidator)
    {
        ArgumentNullException.ThrowIfNull(artifactReferenceValidator);
        this.artifactReferenceValidator = artifactReferenceValidator;
    }

    /// <inheritdoc />
    public IDomainContributionRegistry Create(
        IEnumerable<DomainContributionHandlerRegistration> registrations)
    {
        ArgumentNullException.ThrowIfNull(registrations);
        var supplied = registrations.ToArray();
        if (supplied.Length == 0)
        {
            return new DomainContributionRegistry(
                [],
                ImmutableDictionary<
                    Type,
                    ImmutableArray<DomainContributionHandlerRegistration>>
                    .Empty);
        }

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        var descriptorsValid = ModularityRegistrationOrderer.ValidateDescriptors(
            supplied,
            static registration => registration.Descriptor,
            artifactReferenceValidator,
            "/registrations",
            diagnostics);
        var typesValid = ValidateTypes(supplied, diagnostics);
        if (!descriptorsValid || !typesValid)
        {
            throw CreateException(diagnostics);
        }

        var byType =
            ImmutableDictionary.CreateBuilder<
                Type,
                ImmutableArray<DomainContributionHandlerRegistration>>();
        foreach (var group in supplied
                     .GroupBy(static registration => registration.ContributionType)
                     .OrderBy(
                         static group => group.Key.AssemblyQualifiedName,
                         StringComparer.Ordinal))
        {
            var groupRegistrations = group.ToArray();
            var ordered = ModularityRegistrationOrderer.Order(
                groupRegistrations,
                static registration => registration.Descriptor,
                string.Concat(
                    "/registrations/",
                    group.Key.FullName ?? group.Key.Name),
                diagnostics);
            if (!ordered.IsDefaultOrEmpty)
            {
                byType.Add(group.Key, ordered);
            }
        }

        if (diagnostics.Count > 0)
        {
            throw CreateException(diagnostics);
        }

        var catalogOrder = supplied
            .OrderBy(
                static registration => registration.Descriptor.Registration.Identity.Value,
                StringComparer.Ordinal)
            .ThenBy(
                static registration => registration.Descriptor.Registration.Version.Value,
                StringComparer.Ordinal)
            .ThenBy(
                static registration => registration.Descriptor.Registration.Digest.Value,
                StringComparer.Ordinal)
            .ToImmutableArray();
        return new DomainContributionRegistry(catalogOrder, byType.ToImmutable());
    }

    private static bool ValidateTypes(
        DomainContributionHandlerRegistration[] registrations,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var valid = true;
        for (var index = 0; index < registrations.Length; index++)
        {
            var registration = registrations[index];
            if (registration is null)
            {
                continue;
            }

            var type = registration.ContributionType;
            if (type is null ||
                !typeof(IDomainContribution).IsAssignableFrom(type) ||
                type.IsInterface ||
                type.IsAbstract ||
                type.ContainsGenericParameters)
            {
                diagnostics.Add(ModularityDiagnostics.Error(
                    ModularityDiagnosticIds.InvalidRegistrationType,
                    "A handler registration must name one closed, concrete IDomainContribution type.",
                    string.Concat("/registrations/", index, "/contributionType")));
                valid = false;
            }
        }

        return valid;
    }

    private static ModularityValidationException CreateException(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        new(
            "The domain-contribution registry is invalid.",
            ModularityDiagnostics.Result(diagnostics));
}
