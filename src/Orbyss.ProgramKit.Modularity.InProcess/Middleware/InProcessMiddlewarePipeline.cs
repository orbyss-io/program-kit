using System.Runtime.ExceptionServices;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Modularity.Diagnostics;
using Orbyss.ProgramKit.Modularity.InProcess.Diagnostics;
using Orbyss.ProgramKit.Modularity.Middleware;

namespace Orbyss.ProgramKit.Modularity.InProcess.Middleware;

/// <summary>
/// Executes one frozen middleware registry sequentially in the current process
/// with per-invocation state, deterministic ordering, and single-use next delegates.
/// </summary>
/// <remarks>
/// Once a middleware invokes its next delegate, the pipeline owns and joins
/// that continuation. The delegate's <see cref="ValueTask{TResult}"/> cannot
/// reveal whether its awaiter was consumed, so this implementation does not
/// attempt to infer that. It propagates an owned continuation's failure or
/// cancellation before a middleware failure, then propagates a middleware
/// failure before reporting that the middleware returned while successful
/// downstream work was still running. Middleware can short-circuit by not
/// invoking the continuation, but cannot suppress downstream non-success after
/// invoking it. An already-completed successful continuation is
/// indistinguishable from an awaited one and is therefore accepted.
/// Process-fatal middleware failures propagate immediately without joining a
/// pending continuation; any later continuation fault is still observed.
/// </remarks>
/// <typeparam name="TContext">The exact pipeline context.</typeparam>
/// <typeparam name="TResult">The pipeline result.</typeparam>
public sealed class InProcessMiddlewarePipeline<TContext, TResult> :
    IProgramKitMiddlewarePipeline<TContext, TResult>
{
    private readonly IMiddlewareRegistry<TContext, TResult> registry;

    /// <summary>Initializes the pipeline with one frozen explicit registry.</summary>
    /// <param name="registry">The complete middleware registry selected by the host.</param>
    public InProcessMiddlewarePipeline(
        IMiddlewareRegistry<TContext, TResult> registry)
    {
        ArgumentNullException.ThrowIfNull(registry);
        this.registry = registry;
    }

    /// <inheritdoc />
    public ValueTask<TResult> ExecuteAsync(
        TContext context,
        ProgramKitMiddlewareTerminal<TContext, TResult> terminal,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(terminal);
        cancellationToken.ThrowIfCancellationRequested();
        return InvokeAsync(0, context, terminal, cancellationToken);
    }

    private async ValueTask<TResult> InvokeAsync(
        int index,
        TContext context,
        ProgramKitMiddlewareTerminal<TContext, TResult> terminal,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (index == registry.Registrations.Length)
        {
            try
            {
                var terminalResult =
                    await terminal(context, cancellationToken).ConfigureAwait(false);
                cancellationToken.ThrowIfCancellationRequested();
                return terminalResult;
            }
            catch (Exception exception)
                when (ModularityExceptionBoundary.IsNonFatal(exception))
            {
                cancellationToken.ThrowIfCancellationRequested();
                throw;
            }
        }

        var registration = registry.Registrations[index];
        var continuationGate = new Lock();
        var continuationIsActive = true;
        var nextInvocationCount = 0;
        Task<TResult>? continuationTask = null;
        ValueTask<TResult> Next(TContext nextContext)
        {
            TaskCompletionSource<TResult> completion;
            lock (continuationGate)
            {
                if (!continuationIsActive)
                {
                    throw new ModularityPipelineException(
                        new ProgramKitDiagnostic(
                            ModularityDiagnosticIds
                                .MiddlewareNextInvokedOutsideInvocation,
                            ProgramKitDiagnosticSeverity.Error,
                            string.Concat(
                                "Middleware '",
                                registration.Descriptor.Registration.Identity.Value,
                                "' invoked its next delegate after its invocation ended."),
                            string.Concat("/middleware/", index, "/next")));
                }

                nextInvocationCount++;
                if (nextInvocationCount != 1)
                {
                    throw new ModularityPipelineException(
                        new ProgramKitDiagnostic(
                            ModularityDiagnosticIds
                                .MiddlewareNextInvokedMoreThanOnce,
                            ProgramKitDiagnosticSeverity.Error,
                            string.Concat(
                                "Middleware '",
                                registration.Descriptor.Registration.Identity.Value,
                                "' invoked its next delegate more than once."),
                            string.Concat("/middleware/", index, "/next")));
                }

                cancellationToken.ThrowIfCancellationRequested();
                completion = new TaskCompletionSource<TResult>(
                    TaskCreationOptions.RunContinuationsAsynchronously);
                continuationTask = completion.Task;
            }

            try
            {
                var pending = InvokeAsync(
                    index + 1,
                    nextContext,
                    terminal,
                    cancellationToken);
                if (pending.IsCompletedSuccessfully)
                {
                    completion.SetResult(pending.Result);
                }
                else
                {
                    _ = CompleteContinuationAsync(pending, completion);
                }
            }
            catch (OperationCanceledException exception)
            {
                completion.SetCanceled(exception.CancellationToken);
            }
            catch (Exception exception)
            {
                completion.SetException(exception);
            }

            return new ValueTask<TResult>(completion.Task);
        }

        TResult? middlewareResult = default;
        Exception? middlewareFailure = null;
        Task<TResult>? ownedContinuation = null;
        var middlewareReturnedBeforeContinuationCompleted = false;
        var processFatalFailureEscaping = false;
        try
        {
            middlewareResult = await registration.Middleware
                .InvokeAsync(context, Next, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (Exception exception)
            when (ModularityExceptionBoundary.IsNonFatal(exception))
        {
            middlewareFailure = exception;
        }
        catch (Exception exception)
            when (!ModularityExceptionBoundary.IsNonFatal(exception))
        {
            processFatalFailureEscaping = true;
            throw;
        }
        finally
        {
            lock (continuationGate)
            {
                continuationIsActive = false;
                ownedContinuation = continuationTask;
                middlewareReturnedBeforeContinuationCompleted =
                    ownedContinuation is { IsCompleted: false };
            }

            if (processFatalFailureEscaping)
            {
                ObserveFailure(ownedContinuation);
            }
        }

        Exception? continuationFailure = null;
        if (ownedContinuation is not null)
        {
            try
            {
                _ = await ownedContinuation.ConfigureAwait(false);
            }
            catch (Exception exception)
                when (ModularityExceptionBoundary.IsNonFatal(exception))
            {
                continuationFailure = exception;
            }
        }

        cancellationToken.ThrowIfCancellationRequested();
        if (continuationFailure is not null)
        {
            ExceptionDispatchInfo.Capture(continuationFailure).Throw();
        }

        if (middlewareFailure is not null)
        {
            ExceptionDispatchInfo.Capture(middlewareFailure).Throw();
        }

        if (middlewareReturnedBeforeContinuationCompleted)
        {
            throw new ModularityPipelineException(
                new ProgramKitDiagnostic(
                    ModularityDiagnosticIds.MiddlewareNextNotAwaited,
                    ProgramKitDiagnosticSeverity.Error,
                    string.Concat(
                        "Middleware '",
                        registration.Descriptor.Registration.Identity.Value,
                        "' returned before its next delegate completed; the " +
                        "pipeline joined the owned continuation."),
                    string.Concat("/middleware/", index, "/next")));
        }

        return middlewareResult!;

        static async Task CompleteContinuationAsync(
            ValueTask<TResult> pending,
            TaskCompletionSource<TResult> completion)
        {
            try
            {
                completion.SetResult(await pending.ConfigureAwait(false));
            }
            catch (OperationCanceledException exception)
            {
                completion.SetCanceled(exception.CancellationToken);
            }
            catch (Exception exception)
            {
                completion.SetException(exception);
            }
        }

        static void ObserveFailure(Task<TResult>? continuation)
        {
            if (continuation is null)
            {
                return;
            }

            _ = continuation.ContinueWith(
                static completed => _ = completed.Exception,
                CancellationToken.None,
                TaskContinuationOptions.ExecuteSynchronously |
                TaskContinuationOptions.OnlyOnFaulted,
                TaskScheduler.Default);
        }
    }
}
