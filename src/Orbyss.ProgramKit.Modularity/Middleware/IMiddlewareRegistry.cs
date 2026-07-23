using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Modularity.Middleware;

/// <summary>Provides one immutable exact-signature middleware registration set.</summary>
public interface IMiddlewareRegistry<TContext, TResult>
{
    /// <summary>Gets middleware registrations in deterministic execution order.</summary>
    ImmutableArray<MiddlewareRegistration<TContext, TResult>> Registrations { get; }
}
