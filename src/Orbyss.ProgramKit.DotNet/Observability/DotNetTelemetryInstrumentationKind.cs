namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Finite reviewed framework instrumentation selection.</summary>
public enum DotNetTelemetryInstrumentationKind
{
    /// <summary>ASP.NET Core inbound request instrumentation.</summary>
    AspNetCore,
    /// <summary>System.Net.Http outbound request instrumentation.</summary>
    HttpClient,
}
