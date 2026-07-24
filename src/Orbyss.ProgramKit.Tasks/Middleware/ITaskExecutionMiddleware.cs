using Orbyss.ProgramKit.Modularity.Middleware;

namespace Orbyss.ProgramKit.Tasks.Middleware;

/// <summary>Middleware that runs exactly once per handler attempt.</summary>
public interface ITaskExecutionMiddleware :
    IProgramKitMiddleware<TaskExecutionContext, TaskHandlerInvocationResult>;
