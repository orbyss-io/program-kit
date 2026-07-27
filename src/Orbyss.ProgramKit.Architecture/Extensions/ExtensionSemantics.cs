using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>The union of kind-specific extension semantics.</summary>
public sealed record ExtensionSemantics(
    ReplacementSemantics? Replacement,
    AdditiveContributionSemantics? AdditiveContribution,
    EventSubscriptionSemantics? EventSubscription,
    ProviderSpecializationSemantics? ProviderSpecialization,
    AdapterBridgeSemantics? AdapterBridge);
