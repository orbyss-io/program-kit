namespace Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

/// <summary>Severity of one stable command diagnostic.</summary>
public enum CommandDiagnosticSeverity
{
    /// <summary>Informational observation.</summary>
    Information,

    /// <summary>Non-fatal warning.</summary>
    Warning,

    /// <summary>Operation failure.</summary>
    Error,
}
