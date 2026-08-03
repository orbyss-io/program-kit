using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Cli.Commands;

public static class AuthorityRecordCommand
{
    public static OperationResult Execute(ProgramKitKernel kernel, string workspaceRoot, string requestPath) =>
        kernel.RecordAuthority(workspaceRoot, requestPath);
}
