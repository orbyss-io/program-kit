using Orbyss.ProgramKit.Modularity.Middleware;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;

namespace Orbyss.ProgramKit.Tasks.Middleware;

/// <summary>Middleware that runs exactly once before task acceptance.</summary>
public interface ITaskDispatchMiddleware :
    IProgramKitMiddleware<TaskDispatchContext, TaskDispatchResult>;
