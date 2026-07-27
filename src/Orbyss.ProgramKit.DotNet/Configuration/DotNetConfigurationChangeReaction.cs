namespace Orbyss.ProgramKit.DotNet.Configuration;

/// <summary>Bounded behavior requested after a validated monitored change.</summary>
public enum DotNetConfigurationChangeReaction
{
    /// <summary>No callback scaffolding is generated.</summary>
    None,
    /// <summary>Emit only a redacted diagnostic with no values or references.</summary>
    RedactedDiagnostic,
    /// <summary>Queue the value for a bounded consumer-owned background reaction.</summary>
    ConsumerOwnedQueue,
}
