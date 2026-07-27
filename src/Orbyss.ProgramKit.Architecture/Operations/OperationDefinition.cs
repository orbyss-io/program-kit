using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Operations;

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
