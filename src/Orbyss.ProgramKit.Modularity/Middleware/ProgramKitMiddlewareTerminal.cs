namespace Orbyss.ProgramKit.Modularity.Middleware;

/// <summary>Executes the terminal operation after the selected middleware.</summary>
/// <typeparam name="TContext">The explicit pipeline context.</typeparam>
/// <typeparam name="TResult">The pipeline result.</typeparam>
/// <param name="context">The final middleware context.</param>
/// <param name="cancellationToken">The caller-controlled cancellation token.</param>
public delegate ValueTask<TResult> ProgramKitMiddlewareTerminal<TContext, TResult>(
    TContext context,
    CancellationToken cancellationToken);
