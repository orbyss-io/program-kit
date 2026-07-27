using Orbyss.ProgramKit.Tasks.Core.Instances;

namespace Orbyss.ProgramKit.Tasks.InProcess.Execution;

internal sealed record InProcessTaskWorkItem(
    TaskInstance Instance,
    Type RequestType,
    Type ResponseType,
    object Request,
    CancellationToken ExecutionCancellationToken);
