namespace Orbyss.ProgramKit.DevContainers.Contracts.Diagnostics;

/// <summary>One stable Dev Container validation or generation failure.</summary>
public sealed class DevContainerGenerationException : Exception
{
    internal DevContainerGenerationException(string diagnosticId, string path, string message)
        : base(string.Concat(diagnosticId, " ", path, ": ", message))
    {
        DiagnosticId = diagnosticId;
        Path = path;
    }

    /// <summary>Gets the stable diagnostic identifier.</summary>
    public string DiagnosticId { get; }

    /// <summary>Gets the JSON-pointer-like failure location.</summary>
    public string Path { get; }
}
