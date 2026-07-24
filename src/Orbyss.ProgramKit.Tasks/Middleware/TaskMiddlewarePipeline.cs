using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Middleware;

/// <summary>Default typed task middleware-pipeline coordinator.</summary>
internal sealed class TaskMiddlewarePipeline : ITaskMiddlewarePipeline
{
    /// <inheritdoc />
    public ValueTask<TaskDispatchResult> ExecuteDispatchAsync(
        IServiceProvider services,
        IReadOnlyList<TaskMiddlewareRegistration> registrations,
        TaskDispatchContext context,
        ProgramKitMiddlewareTerminal<TaskDispatchContext, TaskDispatchResult> terminal,
        CancellationToken cancellationToken) =>
        ExecuteAsync<ITaskDispatchMiddleware, TaskDispatchContext, TaskDispatchResult>(
            services,
            registrations,
            context,
            terminal,
            cancellationToken);

    /// <inheritdoc />
    public ValueTask<TaskHandlerInvocationResult> ExecuteAttemptAsync(
        IServiceProvider services,
        IReadOnlyList<TaskMiddlewareRegistration> registrations,
        TaskExecutionContext context,
        ProgramKitMiddlewareTerminal<TaskExecutionContext, TaskHandlerInvocationResult> terminal,
        CancellationToken cancellationToken) =>
        ExecuteAsync<ITaskExecutionMiddleware, TaskExecutionContext, TaskHandlerInvocationResult>(
            services,
            registrations,
            context,
            terminal,
            cancellationToken);

    private static ValueTask<TResult> ExecuteAsync<TMiddleware, TContext, TResult>(
        IServiceProvider services,
        IReadOnlyList<TaskMiddlewareRegistration> registrations,
        TContext context,
        ProgramKitMiddlewareTerminal<TContext, TResult> terminal,
        CancellationToken cancellationToken)
        where TMiddleware : IProgramKitMiddleware<TContext, TResult>
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(registrations);
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(terminal);

        ProgramKitMiddlewareNext<TContext, TResult> continuation =
            current => terminal(current, cancellationToken);
        for (var index = registrations.Count - 1; index >= 0; index--)
        {
            var registration = registrations[index];
            var middleware = services.GetRequiredService(
                registration.MiddlewareType);
            if (middleware is not TMiddleware typed)
            {
                throw new InvalidOperationException(
                    $"Task middleware '{registration.MiddlewareType}' does not implement '{typeof(TMiddleware)}'.");
            }

            var next = continuation;
            continuation = current =>
                typed.InvokeAsync(current, next, cancellationToken);
        }

        return continuation(context);
    }
}
