using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Cli.Commands;

public static class PrepareCommand
{
    public static OperationResult Execute(ProgramKitKernel kernel, string workspaceRoot, string requestPath) =>
        kernel.Prepare(workspaceRoot, requestPath);
}
