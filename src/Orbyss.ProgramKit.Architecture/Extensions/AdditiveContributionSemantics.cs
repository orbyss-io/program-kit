using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>Required semantics for an additive contribution extension point.</summary>
public sealed record AdditiveContributionSemantics(
    string Cardinality,
    string StableOrdering,
    string AggregationSemantics,
    string PartialOrFailFastSemantics);
