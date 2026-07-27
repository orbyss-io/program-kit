using Orbyss.ProgramKit.Modularity.Ordering;

namespace Orbyss.ProgramKit.Modularity.Middleware;

/// <summary>Explicitly binds a stable descriptor to one generic middleware stage.</summary>
/// <typeparam name="TContext">The exact pipeline context.</typeparam>
/// <typeparam name="TResult">The exact pipeline result.</typeparam>
public sealed class MiddlewareRegistration<TContext, TResult> : IModularityRegistration
{
    /// <summary>Initializes one immutable explicit middleware registration.</summary>
    /// <param name="descriptor">The exact identity, owner, and order.</param>
    /// <param name="middleware">The middleware instance selected by the host.</param>
    public MiddlewareRegistration(
        ModularityRegistrationDescriptor descriptor,
        IProgramKitMiddleware<TContext, TResult> middleware)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        ArgumentNullException.ThrowIfNull(middleware);
        Descriptor = descriptor;
        Middleware = middleware;
    }

    /// <inheritdoc />
    public ModularityRegistrationDescriptor Descriptor { get; }

    /// <summary>Gets the explicitly registered middleware instance.</summary>
    public IProgramKitMiddleware<TContext, TResult> Middleware { get; }
}
