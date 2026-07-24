using Orbyss.ProgramKit.Tasks.Core.Attempts;

namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>Consumer-owned typed task behavior.</summary>
/// <typeparam name="TRequest">The typed request model.</typeparam>
/// <typeparam name="TResponse">The typed response model.</typeparam>
public interface ITaskHandler<in TRequest, TResponse>
    where TRequest : notnull
    where TResponse : notnull
{
    /// <summary>Handles one attempt in its exact activation context.</summary>
    ValueTask<TResponse> HandleAsync(
        TaskHandlerContext context,
        TRequest request,
        CancellationToken cancellationToken);
}
