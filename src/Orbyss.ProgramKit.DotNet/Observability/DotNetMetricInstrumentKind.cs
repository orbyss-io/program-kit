namespace Orbyss.ProgramKit.DotNet.Observability;

/// <summary>Finite System.Diagnostics.Metrics instrument selection.</summary>
public enum DotNetMetricInstrumentKind
{
    /// <summary>A monotonic count.</summary>
    Counter,
    /// <summary>A distribution of recorded measurements.</summary>
    Histogram,
}
