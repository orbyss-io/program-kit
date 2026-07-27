using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities;

/// <summary>Controlled capability catalog or bundle failure.</summary>
public sealed class CapabilityOperationException : Exception
{
    /// <summary>Initializes one controlled capability operation failure.</summary>
    public CapabilityOperationException(
        CommandExitCode exitCode,
        string diagnosticId,
        string path,
        string message)
        : base(message)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(diagnosticId);
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        ExitCode = exitCode;
        DiagnosticId = diagnosticId;
        Path = path;
    }

    /// <summary>Gets the stable command exit classification.</summary>
    public CommandExitCode ExitCode { get; }

    /// <summary>Gets the stable diagnostic identifier.</summary>
    public string DiagnosticId { get; }

    /// <summary>Gets the diagnostic path.</summary>
    public string Path { get; }
}
