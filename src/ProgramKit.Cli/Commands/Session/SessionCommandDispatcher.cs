using System;
using System.IO;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.SessionIntegration.Publication;

namespace Orbyss.ProgramKit.Cli.Commands.Session;

public sealed class SessionCommandDispatcher
{
    private readonly SessionIntegrationServices services;

    public SessionCommandDispatcher(SessionIntegrationServices services)
    {
        this.services = services;
    }

    public OperationResult Execute(CliInvocation invocation, string workspace, string request)
    {
        try
        {
            return invocation.Command switch
            {
                PublicCommand.SessionExplain => new ExplainSessionIntegrationOperation(services).Execute(workspace, request),
                PublicCommand.SessionInstall => new InstallSessionIntegrationOperation(services).Execute(workspace, request),
                PublicCommand.SessionVerify => new VerifySessionIntegrationOperation(services).Execute(workspace, request),
                _ => Invalid(invocation.Command, "The session lifecycle operation is not implemented."),
            };
        }
        catch (UnauthorizedAccessException exception) { return Failure(invocation.Command, DiagnosticIds.MissingAuthority, OperationPhase.Validation, PrimaryDisposition.RequestApproval, exception.Message); }
        catch (IOException exception) { return Failure(invocation.Command, DiagnosticIds.Collision, OperationPhase.Publication, PrimaryDisposition.Repair, exception.Message); }
        catch (Exception exception) when (exception is InvalidDataException or InvalidOperationException or FormatException or System.Text.Json.JsonException)
        {
            return Failure(invocation.Command, DiagnosticIds.InvalidInput, OperationPhase.Validation, exception.Message.Contains("source-authoring", StringComparison.OrdinalIgnoreCase) ? PrimaryDisposition.Stop : PrimaryDisposition.Revise, exception.Message);
        }
    }

    private static OperationResult Invalid(PublicCommand command, string message) => Failure(command, DiagnosticIds.InvalidInput, OperationPhase.Request, PrimaryDisposition.Revise, message);

    private static OperationResult Failure(PublicCommand command, string id, OperationPhase phase, PrimaryDisposition disposition, string message)
    {
        Diagnostic diagnostic = DiagnosticFactory.Create(id, phase, "session-integration", message, "No session integration effect was admitted.");
        return OperationResultFactory.Failure(command, OperationOutcome.Blocked, phase, EffectState.None, disposition, new[] { diagnostic });
    }
}
