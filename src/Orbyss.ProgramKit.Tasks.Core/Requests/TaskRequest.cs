namespace Orbyss.ProgramKit.Tasks.Core.Requests;

/// <summary>A rejectable proposal before a task instance exists.</summary>
/// <typeparam name="TRequest">The consumer-owned typed request model.</typeparam>
public sealed record TaskRequest<TRequest>(
    ArtifactReference Revision,
    ArtifactReference DefinitionRevision,
    ArtifactReference RequestContract,
    ArtifactReference ResponseContract,
    ArtifactReference FailureContract,
    ProgramKitIdentifier RequestedBy,
    DateTimeOffset RequestedAt,
    TRequest Payload,
    string? IdempotencyKey,
    ImmutableArray<ArtifactReference> CausalReferences,
    ArtifactReference? OccurrenceRevision)
    where TRequest : notnull;
