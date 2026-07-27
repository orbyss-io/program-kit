using Orbyss.ProgramKit.Tasks.Core.Requests;
using Orbyss.ProgramKit.Tasks.Core.Results;

namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>Runs a typed request through acceptance to a terminal outcome.</summary>
public interface ITaskRunner
{
    /// <summary>Runs immediate work and awaits its terminal result.</summary>
    ValueTask<TaskExecutionOutcome<TResponse>> RunAsync<TRequest, TResponse>(
        TaskRequest<TRequest> request,
        CancellationToken cancellationToken)
        where TRequest : notnull
        where TResponse : notnull;
}
