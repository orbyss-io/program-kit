using System;
using System.IO;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Contracts.Diagnostics;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Diagnostics;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;
using Orbyss.ProgramKit.SessionIntegration.Publication;

namespace Orbyss.ProgramKit.Cli.Commands.Session;

public sealed class SessionCommandDispatcher
{
    private readonly SessionIntegrationServices services;

    public SessionCommandDispatcher(SessionIntegrationServices services)
    {
        this.services = services;
    }

    public OperationResult Execute(CliInvocation invocation, string workspace, string request) =>
        SessionFailureBoundary.Execute(invocation.Command, () => ExecuteCore(invocation, workspace, request));

    private OperationResult ExecuteCore(CliInvocation invocation, string workspace, string request)
    {
        try
        {
            return invocation.Command switch
            {
                PublicCommand.SessionExplain => new ExplainSessionIntegrationOperation(services).Execute(workspace, request),
                PublicCommand.SessionInstall => new InstallSessionIntegrationOperation(services).Execute(workspace, request),
                PublicCommand.SessionVerify => new VerifySessionIntegrationOperation(services).Execute(workspace, request),
                PublicCommand.SessionRemove => new RemoveSessionIntegrationOperation(services).Execute(workspace, request),
                _ => Invalid(invocation.Command, "The session lifecycle operation is not implemented."),
            };
        }
        catch (AmbiguousSessionSelectionException exception)
        {
            return Failure(invocation.Command, DiagnosticIds.AmbiguousSelection, OperationPhase.Resolution, PrimaryDisposition.ProvideInput, exception.Message, EffectState.None, OperationOutcome.NeedsInput);
        }
        catch (UnauthorizedAccessException exception) { return Failure(invocation.Command, DiagnosticIds.MissingAuthority, OperationPhase.Validation, PrimaryDisposition.RequestApproval, exception.Message); }
        catch (InvalidOperationException exception) when (exception.Message.Contains("Stale publication staging", StringComparison.Ordinal))
        {
            return Failure(invocation.Command, DiagnosticIds.InterruptedPublication, OperationPhase.Publication, PrimaryDisposition.Repair, exception.Message, EffectState.Indeterminate);
        }
        catch (IOException exception) { return Failure(invocation.Command, DiagnosticIds.Collision, OperationPhase.Publication, PrimaryDisposition.Repair, exception.Message); }
        catch (Exception exception) when (exception is InvalidDataException or InvalidOperationException or FormatException or System.Text.Json.JsonException)
        {
            return Failure(invocation.Command, DiagnosticIds.InvalidInput, OperationPhase.Validation, PrimaryDisposition.Revise, exception.Message);
        }
    }

    private static OperationResult Invalid(PublicCommand command, string message) => Failure(command, DiagnosticIds.InvalidInput, OperationPhase.Request, PrimaryDisposition.Revise, message);

    private static OperationResult Failure(PublicCommand command, string id, OperationPhase phase, PrimaryDisposition disposition, string message, EffectState effectState = EffectState.None, OperationOutcome outcome = OperationOutcome.Blocked)
    {
        Diagnostic diagnostic = DiagnosticFactory.Create(
            id,
            phase,
            DisclosureFilter.PublicText("session-integration"),
            DisclosureFilter.Withhold(message, "session-command-failure-detail"),
            DisclosureFilter.PublicText("No session integration effect was admitted."));
        return OperationResultFactory.Failure(command, outcome, phase, effectState, disposition, new[] { diagnostic });
    }
}
