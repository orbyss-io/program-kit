using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Middleware;

/// <summary>Executes the frozen dispatch and per-attempt middleware pipelines.</summary>
public interface ITaskMiddlewarePipeline
{
    /// <summary>Executes dispatch middleware once before acceptance.</summary>
    ValueTask<TaskDispatchResult> ExecuteDispatchAsync(
        IServiceProvider services,
        IReadOnlyList<TaskMiddlewareRegistration> registrations,
        TaskDispatchContext context,
        ProgramKitMiddlewareTerminal<TaskDispatchContext, TaskDispatchResult> terminal,
        CancellationToken cancellationToken);

    /// <summary>Executes execution middleware once for one handler attempt.</summary>
    ValueTask<TaskHandlerInvocationResult> ExecuteAttemptAsync(
        IServiceProvider services,
        IReadOnlyList<TaskMiddlewareRegistration> registrations,
        TaskExecutionContext context,
        ProgramKitMiddlewareTerminal<TaskExecutionContext, TaskHandlerInvocationResult> terminal,
        CancellationToken cancellationToken);
}
