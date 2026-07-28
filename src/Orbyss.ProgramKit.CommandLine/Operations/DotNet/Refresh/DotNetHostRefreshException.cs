using Orbyss.ProgramKit.CommandLine.Contracts;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Expected fail-closed refresh rejection.</summary>
public sealed class DotNetHostRefreshException : Exception
{
    /// <summary>Initializes one stable refresh diagnostic.</summary>
    public DotNetHostRefreshException(
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

    /// <summary>Gets the stable diagnostic identity.</summary>
    public string DiagnosticId { get; }

    /// <summary>Gets the frozen Program Kit exit code.</summary>
    public CommandExitCode ExitCode { get; }

    /// <summary>Gets the request-relative diagnostic path.</summary>
    public string Path { get; }
}
