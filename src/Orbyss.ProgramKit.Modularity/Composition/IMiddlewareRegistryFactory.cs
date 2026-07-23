using Orbyss.ProgramKit.Modularity.Middleware;

namespace Orbyss.ProgramKit.Modularity.Composition;

/// <summary>Creates validated immutable generic middleware registries.</summary>
public interface IMiddlewareRegistryFactory
{
    /// <summary>Creates one exact generic middleware registry.</summary>
    IMiddlewareRegistry<TContext, TResult> Create<TContext, TResult>(
        IEnumerable<MiddlewareRegistration<TContext, TResult>> registrations);
}
