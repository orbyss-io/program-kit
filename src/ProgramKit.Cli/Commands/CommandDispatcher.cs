using System;
using System.IO;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Cli.Commands;

public sealed class CommandDispatcher
{
    private readonly ProgramKitKernel kernel;

    public CommandDispatcher(ProgramKitKernel kernel)
    {
        this.kernel = kernel;
    }

    public OperationResult Execute(CliInvocation invocation)
    {
        if (invocation.Command is PublicCommand.Help)
        {
            return ProgramKitKernel.Help();
        }

        if (invocation.Command is PublicCommand.Version)
        {
            return ProgramKitKernel.Version();
        }

        string workspace = Path.GetFullPath(invocation.Workspace!);
        if (!Directory.Exists(workspace))
        {
            return Invalid(invocation.Command, "The workspace directory does not exist.");
        }

        string request = Path.GetFullPath(invocation.Request!);
        if (!request.StartsWith(workspace.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)
            || !File.Exists(request)
            || (File.GetAttributes(request) & FileAttributes.ReparsePoint) != 0)
        {
            return Invalid(invocation.Command, "The request must be a regular file inside the workspace.");
        }

        return invocation.Command switch
        {
            PublicCommand.Explain => kernel.Explain(workspace, request),
            PublicCommand.Construct => kernel.Construct(workspace, request),
            PublicCommand.Evaluate => kernel.Evaluate(workspace, request),
            _ => Invalid(invocation.Command, "Unsupported public command."),
        };
    }

    private static OperationResult Invalid(PublicCommand command, string cause)
    {
        Diagnostic diagnostic = DiagnosticFactory.Create(
            DiagnosticIds.InvalidInput,
            OperationPhase.Request,
            "command-line",
            cause,
            "The command was refused before any workspace effect.");
        return OperationResultFactory.Failure(command, OperationOutcome.Blocked, OperationPhase.Request, EffectState.None, PrimaryDisposition.Revise, new[] { diagnostic });
    }
}
