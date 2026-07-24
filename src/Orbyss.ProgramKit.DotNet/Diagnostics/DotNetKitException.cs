namespace Orbyss.ProgramKit.DotNet.Diagnostics;

/// <summary>Represents one stable .NET kit validation or generation failure.</summary>
public sealed class DotNetKitException : Exception
{
    private DotNetKitException(
        string diagnosticId,
        string message,
        string path,
        Exception? innerException)
        : base(string.Concat(diagnosticId, " ", path, ": ", message), innerException)
    {
        DiagnosticId = diagnosticId;
        Path = path;
    }

    /// <summary>Gets the stable diagnostic identifier.</summary>
    public string DiagnosticId { get; }

    /// <summary>Gets the JSON-pointer-like failure location.</summary>
    public string Path { get; }

    internal static DotNetKitException Create(
        string diagnosticId,
        string message,
        string path,
        Exception? innerException = null) =>
        new(diagnosticId, message, path, innerException);
}
