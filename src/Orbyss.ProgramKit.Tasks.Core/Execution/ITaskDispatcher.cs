using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Requests;

namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>Submits typed work to bounded background acceptance.</summary>
public interface ITaskDispatcher
{
    /// <summary>Returns after acceptance or rejection, before terminal execution.</summary>
    ValueTask<TaskDispatchResult> DispatchAsync<TRequest>(
        TaskRequest<TRequest> request,
        CancellationToken cancellationToken)
        where TRequest : notnull;
}
