using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

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
