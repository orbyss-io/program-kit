namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Finite reviewed trace sampler selection.</summary>
public enum DotNetTelemetrySamplerKind
{
    /// <summary>Record every root trace.</summary>
    AlwaysOn,
    /// <summary>Record no root traces.</summary>
    AlwaysOff,
    /// <summary>Respect the parent decision and ratio-sample root traces.</summary>
    ParentBasedTraceIdRatio,
}
