using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Development.Routing;

/// <summary>Binds a routing outcome to the exact intent and availability snapshot that produced it.</summary>
public sealed record DevelopmentRoutingResult(
    ArtifactReference RequestOrIntent,
    ArtifactReference AvailabilitySnapshot,
    DevelopmentRoutingOutcome Outcome);
