using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>Required semantics for an adapter or bridge.</summary>
public sealed record AdapterBridgeSemantics(
    ProgramKitIdentifier FirstSideOwnerId,
    ProgramKitIdentifier SecondSideOwnerId,
    string TranslationSemantics,
    string LossPolicy,
    string AuthoritySemantics,
    string FailureSemantics,
    string ObservabilitySemantics);
