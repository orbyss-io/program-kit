using Orbyss.ProgramKit.Tasks.Core.Attempts;

namespace Orbyss.ProgramKit.Tasks.Middleware;

/// <summary>Explicit non-durable context for one handler attempt.</summary>
public sealed record TaskExecutionContext(
    TaskHandlerContext HandlerContext,
    Type RequestType,
    Type ResponseType,
    object Request);
