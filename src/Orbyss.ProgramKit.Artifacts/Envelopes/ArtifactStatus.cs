using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Envelopes;

/// <summary>The implementation maturity of an artifact, independent of review or approval state.</summary>
public enum ArtifactStatus
{
    /// <summary>The claimed behavior is implemented.</summary>
    Implemented,

    /// <summary>Only a deliberate scaffold exists.</summary>
    Scaffolded,

    /// <summary>Implementation is deliberately postponed.</summary>
    Deferred,

    /// <summary>The artifact records a possible future outcome.</summary>
    Aspirational,
}
