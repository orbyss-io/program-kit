using Orbyss.ProgramKit.Tasks.Core.Results;

namespace Orbyss.ProgramKit.Tasks.InProcess.Execution;

internal sealed record TaskHandlerResult(
    object? Response,
    TaskFailure? Failure,
    TaskExecutionOutcomeKind Kind);
