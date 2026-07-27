using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Diagnostics;

/// <summary>An operation failure carrying one stable Program Kit JSON diagnostic.</summary>
public sealed class ProgramKitJsonException : Exception
{
    /// <summary>Initializes an operation failure.</summary>
    public ProgramKitJsonException(ProgramKitDiagnostic diagnostic)
        : base(RequireDiagnostic(diagnostic).Message)
    {
        Diagnostic = diagnostic;
    }

    /// <summary>Initializes an operation failure caused by another exception.</summary>
    public ProgramKitJsonException(
        ProgramKitDiagnostic diagnostic,
        Exception innerException)
        : base(RequireDiagnostic(diagnostic).Message, innerException)
    {
        Diagnostic = diagnostic;
    }

    /// <summary>Gets the stable typed diagnostic.</summary>
    public ProgramKitDiagnostic Diagnostic { get; }

    internal static ProgramKitJsonException Create(
        string id,
        string message,
        string path = "",
        Exception? innerException = null)
    {
        var diagnostic = new ProgramKitDiagnostic(
            id,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path);
        return innerException is null
            ? new ProgramKitJsonException(diagnostic)
            : new ProgramKitJsonException(diagnostic, innerException);
    }

    private static ProgramKitDiagnostic RequireDiagnostic(ProgramKitDiagnostic diagnostic)
    {
        ArgumentNullException.ThrowIfNull(diagnostic);
        return diagnostic;
    }
}
