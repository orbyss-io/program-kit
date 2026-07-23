using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Planning;

namespace Orbyss.ProgramKit.Development;

/// <summary>Identifies whether a human-session capability is registered for use.</summary>
public enum CapabilityAvailabilityStatus
{
    /// <summary>The capability is registered and available to the human session.</summary>
    Available,
    /// <summary>The capability is not available to the human session.</summary>
    Unavailable,
}

/// <summary>Records the availability of one capability without interpreting implementation state.</summary>
public sealed record CapabilityAvailability(
    ProgramKitIdentifier CapabilityId,
    CapabilityAvailabilityStatus Status);

/// <summary>
/// Carries the human-session supplied capability-index snapshot used by routing.
/// Program Kit does not read the index implicitly.
/// </summary>
public sealed record CapabilityAvailabilitySnapshot(
    string SourcePath,
    Sha256Digest SourceDigest,
    ImmutableArray<CapabilityAvailability> Capabilities,
    ProgramKitIdentifier SupplierId,
    DateTimeOffset SuppliedAt);

/// <summary>Identifies all supported development routing outcomes.</summary>
public enum DevelopmentRoutingOutcomeKind
{
    /// <summary>The request was routed, optionally naming one next capability.</summary>
    Routed,
    /// <summary>The flow must stop for an explicit human decision.</summary>
    HumanDecisionRequired,
    /// <summary>No supported development flow is available.</summary>
    FlowUnavailable,
}

/// <summary>
/// Reports a routing outcome with zero or one selected capability. This contract intentionally
/// contains no authority or authorization grant.
/// </summary>
public sealed record DevelopmentRoutingOutcome(
    DevelopmentRoutingOutcomeKind Kind,
    ImmutableArray<ArtifactReference> NextCapabilities,
    string Reason);

/// <summary>Binds a routing outcome to the exact intent and availability snapshot that produced it.</summary>
public sealed record DevelopmentRoutingResult(
    ArtifactReference RequestOrIntent,
    ArtifactReference AvailabilitySnapshot,
    DevelopmentRoutingOutcome Outcome);

/// <summary>Identifies the observed result of a human-led development capability invocation.</summary>
public enum DevelopmentResultKind
{
    /// <summary>The capability completed its bounded work.</summary>
    Completed,
    /// <summary>The capability refused work that was not eligible.</summary>
    Refused,
    /// <summary>The attempted capability work failed.</summary>
    Failed,
}

/// <summary>Records a bounded result and exact produced artifacts.</summary>
public sealed record DevelopmentResult(
    DevelopmentResultKind Kind,
    string Summary,
    ImmutableArray<ArtifactReference> ProducedArtifacts,
    DevelopmentRoutingOutcome? Routing);

/// <summary>
/// Provides evidence of a development-capability invocation without granting implementation,
/// approval, release, or any other authority.
/// </summary>
public sealed record DevelopmentReceipt(
    ArtifactReference Capability,
    ArtifactReference RequestOrIntent,
    ImmutableArray<ArtifactReference> ConsumedArtifacts,
    DevelopmentResult Result,
    ProgramKitIdentifier ProducerId,
    PrincipalReference Principal,
    string CorrelationId,
    DateTimeOffset SuppliedAt);
