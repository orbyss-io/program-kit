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
                definition.Disposition,
                new[] { SessionDiagnosticFactory.Create(exception.DiagnosticId, exception.Phase, "session-integration", exception.Message) });
        }
        catch (Exception)
        {
            return OperationResultFactory.Fallback(command, EffectState.None);
        }
    }
}
