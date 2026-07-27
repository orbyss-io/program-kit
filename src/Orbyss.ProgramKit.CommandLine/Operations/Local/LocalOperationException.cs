using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.Local;

/// <summary>Expected fail-closed local-operation diagnostic.</summary>
public sealed class LocalOperationException : Exception
{
    /// <summary>Initializes one expected diagnostic failure.</summary>
    public LocalOperationException(
        string diagnosticId,
        CommandExitCode exitCode,
        string message,
        string path)
        : base(message)
    {
        DiagnosticId = diagnosticId;
        ExitCode = exitCode;
        Path = path;
    }

    /// <summary>Gets the stable diagnostic identifier.</summary>
    public string DiagnosticId { get; }

    /// <summary>Gets the command exit classification.</summary>
    public CommandExitCode ExitCode { get; }

    /// <summary>Gets the stable logical input path.</summary>
    public string Path { get; }
}
