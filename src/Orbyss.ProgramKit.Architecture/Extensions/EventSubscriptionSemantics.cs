using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>Required semantics for an event/subscription extension point.</summary>
public sealed record EventSubscriptionSemantics(
    string DeliveryGuarantee,
    string OrderingScope,
    string RetrySemantics,
    string DuplicationSemantics,
    string HandlerFailureSemantics);
