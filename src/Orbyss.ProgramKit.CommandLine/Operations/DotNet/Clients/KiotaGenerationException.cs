using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Expected fail-closed foreign-client generation failure.</summary>
public sealed class KiotaGenerationException : Exception
{
    /// <summary>Initializes one stable generation diagnostic.</summary>
    public KiotaGenerationException(
        string diagnosticId,
        string message,
        string path)
        : base(message)
    {
        DiagnosticId = diagnosticId;
        Path = path;
        ExitCode = diagnosticId is
            KiotaGenerationDiagnosticIds.ToolFailure or
            KiotaGenerationDiagnosticIds.LockMismatch or
            KiotaGenerationDiagnosticIds.InvalidOutput
                ? CommandExitCode.ConformanceFailure
                : CommandExitCode.UsageOrInputFailure;
    }

    /// <summary>Gets the stable diagnostic identifier.</summary>
    public string DiagnosticId { get; }

    /// <summary>Gets the stable logical input path.</summary>
    public string Path { get; }

    /// <summary>Gets the command failure classification.</summary>
    public CommandExitCode ExitCode { get; }
}
