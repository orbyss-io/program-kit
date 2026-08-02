using System;
using System.IO;
using Orbyss.ProgramKit.Cli.Commands.Session;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.SessionIntegration.Publication;
namespace Orbyss.ProgramKit.Cli.Commands;

public sealed class CommandDispatcher
{
    private readonly ProgramKitKernel kernel;
    private readonly SessionCommandDispatcher sessions;

    public CommandDispatcher(ProgramKitKernel kernel, SessionIntegrationServices sessionServices)
    {
        this.kernel = kernel;
        sessions = new SessionCommandDispatcher(sessionServices);
    }

    public OperationResult Execute(CliInvocation invocation)
    {
        if (invocation.Command is PublicCommand.Help)
        {
            return HelpCommand.Help();
        }

        if (invocation.Command is PublicCommand.Version)
        {
            return HelpCommand.Version();
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
            PublicCommand.SessionExplain => sessions.Execute(invocation, workspace, request),
            PublicCommand.SessionInstall => sessions.Execute(invocation, workspace, request),
            PublicCommand.SessionVerify => sessions.Execute(invocation, workspace, request),
            PublicCommand.SessionRemove => sessions.Execute(invocation, workspace, request),
            _ => Invalid(invocation.Command, "Unsupported public command."),
        };
    }

    private static OperationResult Invalid(PublicCommand command, string cause)
    {
        Diagnostic diagnostic = DiagnosticFactory.Create(
            DiagnosticIds.InvalidInput,
            OperationPhase.Request,
            DisclosureFilter.PublicText("command-line"),
            DisclosureFilter.PublicText(cause),
            DisclosureFilter.PublicText("The command was refused before any workspace effect."));
        return OperationResultFactory.Failure(command, OperationOutcome.Blocked, OperationPhase.Request, EffectState.None, PrimaryDisposition.Revise, new[] { diagnostic });
    }
}
