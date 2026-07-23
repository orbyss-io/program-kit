namespace Orbyss.ProgramKit.Modularity.Middleware;

/// <summary>Invokes the next generic middleware stage or terminal operation.</summary>
/// <typeparam name="TContext">The explicit pipeline context.</typeparam>
/// <typeparam name="TResult">The pipeline result.</typeparam>
/// <param name="context">The context supplied to the next stage.</param>
public delegate ValueTask<TResult> ProgramKitMiddlewareNext<TContext, TResult>(
    TContext context);
