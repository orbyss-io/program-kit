using Orbyss.ProgramKit.Artifacts.Validation;

namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal static class ModularityTestComposition
{
    internal static IDomainContributionRegistryFactory
        CreateDomainContributionRegistryFactory()
    {
        IProgramKitSemanticValidator<ArtifactReference> validator =
            new ArtifactReferenceValidator();
        return new DomainContributionRegistryFactory(validator);
    }

    internal static IDomainContributionRegistry CreateDomainContributionRegistry(
        IEnumerable<DomainContributionHandlerRegistration> registrations)
    {
        var factory = CreateDomainContributionRegistryFactory();
        return factory.Create(registrations);
    }

    internal static IMiddlewareRegistryFactory CreateMiddlewareRegistryFactory()
    {
        IProgramKitSemanticValidator<ArtifactReference> validator =
            new ArtifactReferenceValidator();
        return new MiddlewareRegistryFactory(validator);
    }

    internal static IMiddlewareRegistry<TContext, TResult>
        CreateMiddlewareRegistry<TContext, TResult>(
            IEnumerable<MiddlewareRegistration<TContext, TResult>> registrations)
    {
        var factory = CreateMiddlewareRegistryFactory();
        return factory.Create(registrations);
    }
}
