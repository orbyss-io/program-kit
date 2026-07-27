namespace Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

/// <summary>Represents one expected command grammar failure.</summary>
public sealed class CommandInvocationException : Exception
{
    /// <summary>Initializes a stable invocation failure.</summary>
    public CommandInvocationException(string message, string path = "")
        : base(message)
    {
        Path = path;
    }

    /// <summary>Gets the command-path location associated with the failure.</summary>
    public string Path { get; }
}
