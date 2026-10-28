using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Execution.Core;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Application-owned orchestration; this example promises no atomic write/read snapshot or retry.</summary>
public sealed class LabelOperations(
    ILabelStore store,
    IExecutionDeadlineFactory deadlines,
    IOptions<LabelExecutionOptions> options
) : ILabelOperations
{
    /// <inheritdoc />
    public async Task<string> ReadAsync(CancellationToken cancellationToken)
    {
        using var deadline = deadlines.Create(options.Value.Timeout, cancellationToken);
        try
        {
            EnsureCurrent(deadline, cancellationToken);
            var value = await store.ReadAsync(deadline.Token);
            EnsureCurrent(deadline, cancellationToken);
            return value;
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested && deadline.IsExpired)
        {
            throw new TimeoutException("The sample label observation exceeded its complete execution budget.");
        }
    }

    /// <inheritdoc />
    public async Task<string> UpdateAsync(string value, CancellationToken cancellationToken)
    {
        using var deadline = deadlines.Create(options.Value.Timeout, cancellationToken);
        try
        {
            EnsureCurrent(deadline, cancellationToken);
            await store.WriteAsync(value, deadline.Token);
            EnsureCurrent(deadline, cancellationToken);
            var observed = await store.ReadAsync(deadline.Token);
            EnsureCurrent(deadline, cancellationToken);
            return observed;
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested && deadline.IsExpired)
        {
            // A timed-out observation does not undo or retry an already dispatched write.
            throw new TimeoutException("The sample write outcome needs reconciliation after execution expiry.");
        }
    }

    /// <summary>Observes caller priority and monotonic expiry even if the timer callback is delayed.</summary>
    private static void EnsureCurrent(IExecutionDeadline deadline, CancellationToken caller)
    {
        caller.ThrowIfCancellationRequested();
        if (deadline.IsExpired)
            throw new OperationCanceledException(deadline.Token);
        deadline.Token.ThrowIfCancellationRequested();
    }
}
