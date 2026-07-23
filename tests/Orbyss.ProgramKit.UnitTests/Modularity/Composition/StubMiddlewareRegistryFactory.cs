namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal sealed class StubMiddlewareRegistryFactory : IMiddlewareRegistryFactory
{
    public IMiddlewareRegistry<TContext, TResult> Create<TContext, TResult>(
        IEnumerable<MiddlewareRegistration<TContext, TResult>> registrations) =>
        new StubMiddlewareRegistry<TContext, TResult>();
}
