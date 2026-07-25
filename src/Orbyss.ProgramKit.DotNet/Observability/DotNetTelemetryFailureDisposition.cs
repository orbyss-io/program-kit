namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Non-authoritative telemetry failure behavior.</summary>
public enum DotNetTelemetryFailureDisposition
{
    /// <summary>Bound and report exporter failure without changing application success.</summary>
    DropAndReport,
}
