using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Development.Routing;

namespace Orbyss.ProgramKit.Development.Receipts;

/// <summary>Records a bounded result and exact produced artifacts.</summary>
public sealed record DevelopmentResult(
    DevelopmentResultKind Kind,
    string Summary,
    ImmutableArray<ArtifactReference> ProducedArtifacts,
    DevelopmentRoutingOutcome? Routing);
