using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Modularity.Diagnostics;
using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Modularity.Ordering;

namespace Orbyss.ProgramKit.Modularity.Composition;

/// <summary>Default validated middleware registry factory.</summary>
public sealed class MiddlewareRegistryFactory : IMiddlewareRegistryFactory
{
    private readonly IProgramKitSemanticValidator<ArtifactReference>
        artifactReferenceValidator;

    /// <summary>Initializes the factory with its semantic reference validator.</summary>
    public MiddlewareRegistryFactory(
        IProgramKitSemanticValidator<ArtifactReference> artifactReferenceValidator)
    {
        ArgumentNullException.ThrowIfNull(artifactReferenceValidator);
        this.artifactReferenceValidator = artifactReferenceValidator;
    }

    /// <inheritdoc />
    public IMiddlewareRegistry<TContext, TResult> Create<TContext, TResult>(
        IEnumerable<MiddlewareRegistration<TContext, TResult>> registrations)
    {
        ArgumentNullException.ThrowIfNull(registrations);
        var supplied = registrations.ToArray();
        if (supplied.Length == 0)
        {
            return new MiddlewareRegistry<TContext, TResult>([]);
        }

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (!ModularityRegistrationOrderer.ValidateDescriptors(
                supplied,
                static registration => registration.Descriptor,
                artifactReferenceValidator,
                "/registrations",
                diagnostics))
        {
            throw CreateException(diagnostics);
        }

        var ordered = ModularityRegistrationOrderer.Order(
            supplied,
            static registration => registration.Descriptor,
            "/registrations",
            diagnostics);
        if (diagnostics.Count > 0)
        {
            throw CreateException(diagnostics);
        }

        return new MiddlewareRegistry<TContext, TResult>(ordered);
    }

    private static ModularityValidationException CreateException(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics) =>
        new(
            "The middleware registry is invalid.",
            ModularityDiagnostics.Result(diagnostics));
}
