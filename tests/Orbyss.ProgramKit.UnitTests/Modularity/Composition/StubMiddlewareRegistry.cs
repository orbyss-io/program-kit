using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Modularity.Composition;

internal sealed class StubMiddlewareRegistry<TContext, TResult> :
    IMiddlewareRegistry<TContext, TResult>
{
    public ImmutableArray<MiddlewareRegistration<TContext, TResult>>
        Registrations => [];
}
