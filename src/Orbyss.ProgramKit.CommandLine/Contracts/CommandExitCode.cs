namespace Orbyss.ProgramKit.CommandLine.Contracts;

/// <summary>Stable process exit codes exposed by the Program Kit CLI.</summary>
public enum CommandExitCode
{
    /// <summary>The requested operation succeeded.</summary>
    Success = 0,

    /// <summary>The input was understood but did not conform.</summary>
    ConformanceFailure = 1,

    /// <summary>The invocation, explicit input, or file operation was invalid.</summary>
    UsageOrInputFailure = 2,

    /// <summary>An unexpected internal failure occurred.</summary>
    InternalFailure = 3,
}
