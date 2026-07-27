namespace Orbyss.ProgramKit.Tasks.Middleware;

/// <summary>Internal-pipeline result of one typed handler invocation.</summary>
public sealed record TaskHandlerInvocationResult(object Response);
