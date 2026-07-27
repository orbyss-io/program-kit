namespace Orbyss.ProgramKit.Tasks.Core.Bindings;

/// <summary>
/// Exact binding from a task definition to opaque handler, feature activation,
/// runtime, middleware, and policy selections.
/// </summary>
public sealed record TaskActivationBinding(
    ArtifactReference Revision,
    ArtifactReference DefinitionRevision,
    ArtifactReference HandlerRevision,
    ArtifactReference OwningFeatureRevision,
    ProgramKitIdentifier ActivationIdentity,
    ArtifactReference RuntimeRevision,
    ImmutableArray<ArtifactReference> MiddlewareRevisions,
    ArtifactReference RetryPolicyRevision,
    ArtifactReference IdempotencyPolicyRevision,
    ArtifactReference? ScheduleRevision,
    ArtifactReference? MisfirePolicyRevision,
    ArtifactReference? OverlapPolicyRevision);
