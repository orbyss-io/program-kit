using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Ownership;

/// <summary>
/// Classifies the semantic owner responsible for an artifact kind. This is an
/// ownership classification, not an implementation layer or storage location.
/// </summary>
public enum ArtifactOwnershipClassification
{
    /// <summary>A domain owns semantic meaning and public behavior.</summary>
    DomainSemantic,

    /// <summary>A project or package owns a build and distribution boundary.</summary>
    BuildBoundary,

    /// <summary>A producer owns a deterministic projection of canonical inputs.</summary>
    GeneratedProjection,

    /// <summary>A human-started capability owner governs agent procedure.</summary>
    AgentProcedure,

    /// <summary>A human authority owns an explanation or decision record.</summary>
    HumanAuthority,

    /// <summary>A quality owner governs reusable verification meaning.</summary>
    Quality,

    /// <summary>A versioned boundary owner governs compatibility selection.</summary>
    Versioning,

    /// <summary>An impacted semantic or deployable boundary owns migration.</summary>
    Migration,

    /// <summary>A serialization owner governs an exact wire representation.</summary>
    Serialization,

    /// <summary>A domain owns requested-work and schedule meaning.</summary>
    Tasking,

    /// <summary>A host owns selected composition and operational configuration.</summary>
    HostComposition,

    /// <summary>A contract owner bounds state that is deliberately not durable.</summary>
    EphemeralState
}
