using System;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.SessionIntegration.Diagnostics;

public static class SessionFailureBoundary
{
    public static OperationResult Execute(PublicCommand command, Func<OperationResult> operation)
    {
        try
        {
            return operation();
        }
        catch (SessionDiagnosticException exception)
        {
            SessionDiagnosticDefinition definition = SessionDiagnosticCatalog.Get(exception.DiagnosticId);
            return OperationResultFactory.Failure(
                command,
                OperationOutcome.Blocked,
                exception.Phase,
                exception.EffectState,
                ParseDisposition(definition.Disposition),
                new[] { SessionDiagnosticFactory.Create(exception.DiagnosticId, exception.Phase, "session-integration", exception.Message) });
        }
        catch (Exception)
        {
            return OperationResultFactory.Fallback(command, EffectState.None);
        }
    }

    private static PrimaryDisposition ParseDisposition(string value) => value switch
    {
        "complete" => PrimaryDisposition.Complete,
        "retry" => PrimaryDisposition.Retry,
        "provide-input" => PrimaryDisposition.ProvideInput,
        "request-approval" => PrimaryDisposition.RequestApproval,
        "repair" => PrimaryDisposition.Repair,
        "revise" => PrimaryDisposition.Revise,
        _ => PrimaryDisposition.Stop,
    };
}
