namespace Orbyss.ProgramKit.Tasks.Core.Cancellation;

/// <summary>Explicit cancellation request for already accepted work.</summary>
public sealed record TaskCancellationRequest(
    ArtifactReference Revision,
    ArtifactReference InstanceRevision,
    ProgramKitIdentifier RequestedBy,
    DateTimeOffset RequestedAt,
    string ReasonCode,
    ImmutableArray<ArtifactReference> CausalReferences);
