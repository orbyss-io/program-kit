using Orbyss.ProgramKit.Tasks.Core.Cancellation;

namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>Requests cancellation without promising terminal cancellation.</summary>
public interface ITaskCancellationRequester
{
    /// <summary>Records or rejects one explicit cancellation request.</summary>
    ValueTask<TaskCancellationResult> RequestAsync(
        TaskCancellationRequest request,
        CancellationToken cancellationToken);
}
