namespace Orbyss.ProgramKit.Modularity.Middleware;

/// <summary>Executes one immutable generic middleware registry.</summary>
/// <typeparam name="TContext">The exact pipeline context.</typeparam>
/// <typeparam name="TResult">The exact pipeline result.</typeparam>
public interface IProgramKitMiddlewarePipeline<TContext, TResult>
{
    /// <summary>Executes the selected middleware and terminal operation once.</summary>
    /// <param name="context">The explicit pipeline context.</param>
    /// <param name="terminal">The terminal operation.</param>
    /// <param name="cancellationToken">The caller-controlled cancellation token.</param>
    ValueTask<TResult> ExecuteAsync(
        TContext context,
        ProgramKitMiddlewareTerminal<TContext, TResult> terminal,
        CancellationToken cancellationToken = default);
}
