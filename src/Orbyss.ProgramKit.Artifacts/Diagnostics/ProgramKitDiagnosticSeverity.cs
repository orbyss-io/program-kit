using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Diagnostics;

/// <summary>Classifies a Program Kit diagnostic without coupling it to a host or transport.</summary>
public enum ProgramKitDiagnosticSeverity
{
    /// <summary>Additional deterministic information that does not affect validity.</summary>
    Information,

    /// <summary>A condition that deserves attention but does not make the value invalid.</summary>
    Warning,

    /// <summary>A conformance failure.</summary>
    Error,
}
