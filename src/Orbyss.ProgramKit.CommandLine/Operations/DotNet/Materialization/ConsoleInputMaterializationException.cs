using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Expected fail-closed Console input materialization failure.</summary>
public sealed class ConsoleInputMaterializationException : Exception
{
    /// <summary>Initializes one stable materialization diagnostic.</summary>
    public ConsoleInputMaterializationException(
        string diagnosticId,
        string message,
        string path,
        CommandExitCode exitCode = CommandExitCode.ConformanceFailure)
        : base(message)
    {
        DiagnosticId = diagnosticId;
        Path = path;
        ExitCode = exitCode;
    }

    /// <summary>Gets the stable Program Kit diagnostic identifier.</summary>
    public string DiagnosticId { get; }

    /// <summary>Gets the bounded request or artifact path.</summary>
    public string Path { get; }

    /// <summary>Gets the stable process exit class.</summary>
    public CommandExitCode ExitCode { get; }
}
