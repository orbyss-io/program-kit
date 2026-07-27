using System.Collections.Immutable;
namespace Orbyss.ProgramKit.Modularity.Middleware;

/// <summary>
/// Immutable registry for one exact generic middleware pipeline signature.
/// </summary>
/// <typeparam name="TContext">The exact pipeline context.</typeparam>
/// <typeparam name="TResult">The exact pipeline result.</typeparam>
public sealed class MiddlewareRegistry<TContext, TResult> :
    IMiddlewareRegistry<TContext, TResult>
{
    internal MiddlewareRegistry(
        ImmutableArray<MiddlewareRegistration<TContext, TResult>> registrations)
    {
        Registrations = registrations;
    }

    /// <summary>Gets middleware registrations in deterministic execution order.</summary>
    public ImmutableArray<MiddlewareRegistration<TContext, TResult>> Registrations { get; }

}
