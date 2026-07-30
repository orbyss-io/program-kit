using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Expected fail-closed Console request scaffolding failure.</summary>
public sealed class ConsoleRequestScaffoldingException : Exception
{
    /// <summary>Initializes one stable scaffold diagnostic.</summary>
    public ConsoleRequestScaffoldingException(
        string message,
        string path,
        CommandExitCode exitCode = CommandExitCode.ConformanceFailure)
        : base(message)
    {
        Path = path;
        ExitCode = exitCode;
    }

    /// <summary>Gets the exact failed input path.</summary>
    public string Path { get; }

    /// <summary>Gets the stable process exit class.</summary>
    public CommandExitCode ExitCode { get; }
}
