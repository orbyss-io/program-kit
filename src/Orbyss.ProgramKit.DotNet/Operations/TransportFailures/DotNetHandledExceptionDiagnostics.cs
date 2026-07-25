namespace Orbyss.ProgramKit.DotNet.Operations.TransportFailures;

/// <summary>Exact .NET 10 handled-exception diagnostic disposition.</summary>
public enum DotNetHandledExceptionDiagnostics
{
    /// <summary>Suppress framework diagnostics and emit one sanitized Program Kit outcome.</summary>
    SuppressFrameworkAndEmitSanitizedOnce,
}
