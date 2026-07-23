using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture;

/// <summary>The only five extension semantics supported by the baseline.</summary>
public enum ExtensionKind
{
    /// <summary>Select exactly one or zero-or-one implementation.</summary>
    Replacement,

    /// <summary>Combine an ordered set of contributions.</summary>
    AdditiveContribution,

    /// <summary>Deliver a notification to subscriptions.</summary>
    EventSubscription,

    /// <summary>Add a contract to a declared base provider.</summary>
    ProviderSpecialization,

    /// <summary>Translate explicitly owned sides.</summary>
    AdapterBridge
}

/// <summary>Allowed cardinality for a replacement extension.</summary>
public enum ReplacementCardinality
{
    /// <summary>Exactly one implementation must be selected.</summary>
    ExactlyOne,

    /// <summary>Zero or one implementation may be selected.</summary>
    ZeroOrOne
}

/// <summary>
/// An extension point and the semantic fields required by its selected kind.
/// Fields that do not apply to the selected kind remain absent and are rejected
/// when populated, keeping the wire contract non-polymorphic and explicit.
/// </summary>
public sealed record ExtensionDefinition(
    ProgramKitIdentifier Identity,
    ProgramKitIdentifier OwnerId,
    ExtensionKind Kind,
    ArtifactReference Contract,
    ExtensionSemantics Semantics);

/// <summary>The union of kind-specific extension semantics.</summary>
public sealed record ExtensionSemantics(
    ReplacementSemantics? Replacement,
    AdditiveContributionSemantics? AdditiveContribution,
    EventSubscriptionSemantics? EventSubscription,
    ProviderSpecializationSemantics? ProviderSpecialization,
    AdapterBridgeSemantics? AdapterBridge);

/// <summary>Required semantics for a replacement extension point.</summary>
public sealed record ReplacementSemantics(
    ReplacementCardinality Cardinality,
    string SelectionRule,
    string FallbackSemantics,
    string FailureSemantics);

/// <summary>Required semantics for an additive contribution extension point.</summary>
public sealed record AdditiveContributionSemantics(
    string Cardinality,
    string StableOrdering,
    string AggregationSemantics,
    string PartialOrFailFastSemantics);

/// <summary>Required semantics for an event/subscription extension point.</summary>
public sealed record EventSubscriptionSemantics(
    string DeliveryGuarantee,
    string OrderingScope,
    string RetrySemantics,
    string DuplicationSemantics,
    string HandlerFailureSemantics);

/// <summary>Required semantics for a provider specialization.</summary>
public sealed record ProviderSpecializationSemantics(
    ProgramKitIdentifier BaseProviderId,
    ImmutableArray<ArtifactReference> AddedContracts,
    string CompatibilitySemantics,
    string FallbackSemantics);

/// <summary>Required semantics for an adapter or bridge.</summary>
public sealed record AdapterBridgeSemantics(
    ProgramKitIdentifier FirstSideOwnerId,
    ProgramKitIdentifier SecondSideOwnerId,
    string TranslationSemantics,
    string LossPolicy,
    string AuthoritySemantics,
    string FailureSemantics,
    string ObservabilitySemantics);
