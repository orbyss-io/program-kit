using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Development.Routing;

/// <summary>
/// Reports a routing outcome with zero or one selected capability. This contract intentionally
/// contains no authority or authorization grant.
/// </summary>
public sealed record DevelopmentRoutingOutcome(
    DevelopmentRoutingOutcomeKind Kind,
    ImmutableArray<ArtifactReference> NextCapabilities,
    string Reason);
