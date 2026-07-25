namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Finite Microsoft.Extensions.Logging level selection.</summary>
public enum DotNetLogLevel
{
    /// <summary>Detailed tracing information.</summary>
    Trace,
    /// <summary>Developer diagnostic information.</summary>
    Debug,
    /// <summary>Normal operational information.</summary>
    Information,
    /// <summary>A recoverable abnormal condition.</summary>
    Warning,
    /// <summary>An operation failure.</summary>
    Error,
    /// <summary>A critical host failure.</summary>
    Critical,
}
