using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture;

/// <summary>
/// A caller-visible operation with all ten mandatory semantic dimensions.
/// No dimension is inferred from implementation shape.
/// </summary>
public sealed record OperationDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerDomainId,
    string Purpose,
    OperationInputDefinition Input,
    OperationOutputDefinition Output,
    OperationSideEffectDefinition SideEffects,
    OperationAuthorityDefinition Authority,
    OperationFailureSet Failures,
    OperationCancellationDefinition Cancellation,
    OperationIdempotencyDefinition Idempotency,
    OperationCompatibilityDefinition Compatibility,
    OperationObservabilityDefinition Observability,
    OperationResourceOwnershipDefinition ResourceOwnership);

/// <summary>The exact input contract and validation boundary of an operation.</summary>
public sealed record OperationInputDefinition(
    ImmutableArray<ArtifactReference> Contracts,
    bool AllowsNoInput,
    string ValidationSemantics);

/// <summary>The exact output contract and production boundary of an operation.</summary>
public sealed record OperationOutputDefinition(
    ImmutableArray<ArtifactReference> Contracts,
    bool AllowsNoOutput,
    bool IsStreaming,
    string CompletionSemantics);

/// <summary>The side effects an operation may perform.</summary>
public sealed record OperationSideEffectDefinition(
    bool IsSideEffectFree,
    ImmutableArray<OperationSideEffect> Effects);

/// <summary>One explicitly owned side effect.</summary>
public sealed record OperationSideEffect(
    ProgramKitIdentifier OwnerId,
    string Effect,
    string CommitBoundary,
    string CompensationPolicy);

/// <summary>The authority required to invoke and execute an operation.</summary>
public sealed record OperationAuthorityDefinition(
    bool IsRequired,
    ImmutableArray<ProgramKitIdentifier> RequirementIds,
    string EvaluationPoint,
    string DenialSemantics);

/// <summary>The complete stable failure surface of an operation.</summary>
public sealed record OperationFailureSet(
    ImmutableArray<OperationFailureDefinition> DeclaredFailures,
    string UndeclaredFailurePolicy);

/// <summary>One stable failure code and its caller-visible meaning.</summary>
public sealed record OperationFailureDefinition(
    ProgramKitIdentifier Identity,
    string Code,
    string Meaning,
    bool IsRetryable,
    ArtifactReference? DetailsContract);

/// <summary>How an operation accepts, propagates, and observes cancellation.</summary>
public sealed record OperationCancellationDefinition(
    bool IsSupported,
    string AcceptanceSemantics,
    string PropagationSemantics,
    string CompletionRaceSemantics);

/// <summary>The idempotency guarantee of an operation.</summary>
public sealed record OperationIdempotencyDefinition(
    OperationIdempotencyKind Kind,
    string KeySemantics,
    string DuplicateSemantics);

/// <summary>The strength of an operation's idempotency contract.</summary>
public enum OperationIdempotencyKind
{
    /// <summary>Repeated execution is not guaranteed to be equivalent.</summary>
    NonIdempotent,

    /// <summary>The same semantic request can safely be repeated.</summary>
    NaturallyIdempotent,

    /// <summary>An explicit key controls deduplication.</summary>
    IdempotencyKey,

    /// <summary>The caller must supply an optimistic concurrency condition.</summary>
    Conditional
}

/// <summary>The compatibility dimensions exposed by an operation.</summary>
public sealed record OperationCompatibilityDefinition(
    ImmutableArray<CompatibilityDimension> Dimensions,
    string ChangePolicy,
    ImmutableArray<ArtifactReference> MigrationReferences);

/// <summary>The signals and correlation behavior exposed by an operation.</summary>
public sealed record OperationObservabilityDefinition(
    ImmutableArray<string> Signals,
    string CorrelationSemantics,
    string SensitiveDataPolicy);

/// <summary>The resources acquired, released, or transferred by an operation.</summary>
public sealed record OperationResourceOwnershipDefinition(
    ImmutableArray<OperationResourceDefinition> Resources,
    string DisposalSemantics);

/// <summary>One resource and its ownership lifecycle.</summary>
public sealed record OperationResourceDefinition(
    string Resource,
    ProgramKitIdentifier OwnerId,
    string Acquisition,
    string Release,
    bool OwnershipTransfers);
