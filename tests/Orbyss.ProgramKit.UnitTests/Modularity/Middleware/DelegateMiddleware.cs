namespace Orbyss.ProgramKit.UnitTests.Modularity.Middleware;

internal sealed class DelegateMiddleware<TContext, TResult> :
    IProgramKitMiddleware<TContext, TResult>
{
    private readonly Func<
        TContext,
        ProgramKitMiddlewareNext<TContext, TResult>,
        CancellationToken,
        ValueTask<TResult>> action;

    public DelegateMiddleware(
        Func<
            TContext,
            ProgramKitMiddlewareNext<TContext, TResult>,
            CancellationToken,
            ValueTask<TResult>> action)
    {
        this.action = action;
    }

    public ValueTask<TResult> InvokeAsync(
        TContext context,
        ProgramKitMiddlewareNext<TContext, TResult> continuation,
        CancellationToken cancellationToken) =>
        action(context, continuation, cancellationToken);
}
