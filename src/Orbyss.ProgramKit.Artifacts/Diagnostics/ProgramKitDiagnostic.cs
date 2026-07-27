using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Diagnostics;

/// <summary>A stable, transport-independent validation diagnostic.</summary>
/// <param name="Id">The stable diagnostic identifier.</param>
/// <param name="Severity">The diagnostic severity.</param>
/// <param name="Message">The culture-invariant diagnostic message.</param>
/// <param name="Path">The JSON Pointer-like path to the invalid value.</param>
public sealed record ProgramKitDiagnostic(
    string Id,
    ProgramKitDiagnosticSeverity Severity,
    string Message,
    string Path);
