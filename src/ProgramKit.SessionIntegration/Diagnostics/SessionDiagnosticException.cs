using System;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.SessionIntegration.Diagnostics;

public sealed class SessionDiagnosticException : Exception
{
    public SessionDiagnosticException(string diagnosticId, OperationPhase phase, EffectState effectState, string message)
        : base(message)
    {
        DiagnosticId = diagnosticId;
        Phase = phase;
        EffectState = effectState;
    }

    public string DiagnosticId { get; }
    public OperationPhase Phase { get; }
    public EffectState EffectState { get; }
}
