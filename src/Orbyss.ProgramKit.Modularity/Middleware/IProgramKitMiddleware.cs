namespace Orbyss.ProgramKit.Modularity.Middleware;

/// <summary>Defines one generic middleware stage.</summary>
/// <typeparam name="TContext">The explicit pipeline context.</typeparam>
/// <typeparam name="TResult">The pipeline result.</typeparam>
public interface IProgramKitMiddleware<TContext, TResult>
{
    /// <summary>
    /// Invokes this stage. Returning without invoking <paramref name="continuation"/>
    /// deliberately short-circuits the pipeline.
    /// </summary>
    /// <param name="context">The current pipeline context.</param>
    /// <param name="continuation">The single-use next delegate.</param>
    /// <param name="cancellationToken">The caller-controlled cancellation token.</param>
    ValueTask<TResult> InvokeAsync(
        TContext context,
        ProgramKitMiddlewareNext<TContext, TResult> continuation,
        CancellationToken cancellationToken);
}
