namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Strict typed NuGet lock read failure with an exact JSON path.</summary>
public sealed class NuGetLockReadException : Exception
{
    /// <summary>Initializes one exact lock read failure.</summary>
    public NuGetLockReadException(
        string message,
        string path,
        Exception innerException)
        : base(message, innerException)
    {
        Path = path;
    }

    /// <summary>Gets the RFC 6901 path within the NuGet lock.</summary>
    public string Path { get; }
}
