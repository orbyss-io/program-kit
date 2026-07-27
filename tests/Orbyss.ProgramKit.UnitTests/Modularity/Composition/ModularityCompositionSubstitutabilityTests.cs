namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

[TestClass]
public sealed class ModularityCompositionSubstitutabilityTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    public async Task ExternalFactoryRegistriesFlowIntoInProcessConsumers()
    {
        var contributionRegistry = new StubDomainContributionRegistry();
        var contributionFactory =
            new StubDomainContributionRegistryFactory(contributionRegistry);
        var middlewareFactory = new StubMiddlewareRegistryFactory();
        var (publication, result) = await ExerciseFactoriesAsync(
            contributionFactory,
            middlewareFactory,
            TestContext.CancellationToken);

        Assert.IsTrue(publication.Succeeded);
        Assert.IsTrue(publication.Handlers.IsEmpty);
        Assert.AreEqual(4, result);
    }

    private static async Task<(DomainContributionPublicationResult, int)>
        ExerciseFactoriesAsync<TContributionFactory, TMiddlewareFactory>(
            TContributionFactory contributionFactory,
            TMiddlewareFactory middlewareFactory,
            CancellationToken cancellationToken)
        where TContributionFactory : IDomainContributionRegistryFactory
        where TMiddlewareFactory : IMiddlewareRegistryFactory
    {
        var contributionRegistry = contributionFactory.Create([]);
        var publisher =
            new InProcessDomainContributionPublisher(contributionRegistry);

        var publication = await publisher.PublishAsync(
            new RecordedContribution("stub"),
            DomainContributionPublicationPolicy.FailFast,
            cancellationToken);

        var middlewareRegistry =
            middlewareFactory.Create<string, int>([]);
        var pipeline =
            new InProcessMiddlewarePipeline<string, int>(middlewareRegistry);
        var result = await pipeline.ExecuteAsync(
            "stub",
            static (context, _) => ValueTask.FromResult(context.Length),
            cancellationToken);
        return (publication, result);
    }

    [TestMethod]
    public void FactoryContractsReturnRegistryContracts()
    {
        Assert.AreEqual(
            typeof(IDomainContributionRegistry),
            typeof(IDomainContributionRegistryFactory)
                .GetMethod(nameof(IDomainContributionRegistryFactory.Create))!
                .ReturnType);

        var returnType = typeof(IMiddlewareRegistryFactory)
            .GetMethod(nameof(IMiddlewareRegistryFactory.Create))!
            .ReturnType;
        Assert.IsTrue(returnType.IsGenericType);
        Assert.AreEqual(
            typeof(IMiddlewareRegistry<,>),
            returnType.GetGenericTypeDefinition());
    }
}
