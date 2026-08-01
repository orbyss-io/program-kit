using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public sealed class ProgramKitDiagnosticException : System.Exception
{
    public ProgramKitDiagnosticException(
        string diagnosticId,
        OperationPhase phase,
        PrimaryDisposition disposition,
        string message)
        : base(message)
    {
        DiagnosticId = diagnosticId;
        Phase = phase;
        Disposition = disposition;
    }

    public string DiagnosticId { get; }

    public OperationPhase Phase { get; }

    public PrimaryDisposition Disposition { get; }
}
