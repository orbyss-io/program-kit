using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json.Nodes;
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
            PublicCommand.Init or PublicCommand.CatalogList or PublicCommand.Restore or PublicCommand.Prepare or PublicCommand.AuthorityRecord => ExecuteWorkspaceCommand(invocation.Command, workspace, request),
            _ => Invalid(invocation.Command, "Unsupported public command."),
        };
    }

    private OperationResult ExecuteWorkspaceCommand(PublicCommand command, string workspace, string request)
    {
        try
        {
            return command switch
            {
                PublicCommand.Init => kernel.InitializeWorkspace(workspace, request),
                PublicCommand.CatalogList => kernel.ListCatalog(request),
                PublicCommand.Restore => kernel.RestoreWorkspace(workspace, request),
                PublicCommand.Prepare => PrepareCommand.Execute(kernel, workspace, request),
                PublicCommand.AuthorityRecord => Pending(command, "authority-recording"),
                _ => Invalid(command, "Unsupported public command."),
            };
        }
        catch (KeyNotFoundException)
        {
            return WorkspaceFailure(command, DiagnosticIds.MissingSelection, PrimaryDisposition.ProvideInput, "An exact selected item is unavailable.");
        }
        catch (InvalidDataException)
        {
            return Invalid(command, "The request or referenced workspace document is invalid.");
        }
        catch (IOException)
        {
            return WorkspaceFailure(command, DiagnosticIds.GeneratedDrift, PrimaryDisposition.Repair, "Generated workspace state conflicts with the requested exact state.");
        }
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

    private static OperationResult Pending(PublicCommand command, string handler)
    {
        Diagnostic diagnostic = DiagnosticFactory.Create(
            DiagnosticIds.IncompleteMeaning,
            OperationPhase.Validation,
            DisclosureFilter.PublicText(handler),
            DisclosureFilter.PublicText("The typed command handler has no admitted request implementation yet."),
            DisclosureFilter.PublicText("No workspace effect was attempted."));
        return OperationResultFactory.Failure(command, OperationOutcome.Blocked, OperationPhase.Request, EffectState.None, diagnostic.Disposition, new[] { diagnostic }, payload: new JsonObject { ["handler"] = handler });
    }

    private static OperationResult WorkspaceFailure(PublicCommand command, string id, PrimaryDisposition disposition, string cause)
    {
        Diagnostic diagnostic = DiagnosticFactory.Create(
            id,
            OperationPhase.Validation,
            DisclosureFilter.PublicText("workspace-request"),
            DisclosureFilter.PublicText(cause),
            DisclosureFilter.PublicText("No requested workspace state was admitted."));
        if (diagnostic.Disposition != disposition) throw new InvalidOperationException("The requested failure disposition does not match its diagnostic catalog.");
        return OperationResultFactory.Failure(command, OperationOutcome.Blocked, OperationPhase.Workspace, EffectState.None, disposition, new[] { diagnostic });
    }
}
