namespace Orbyss.ProgramKit.Development.Routing;

/// <summary>Identifies all supported development routing outcomes.</summary>
public enum DevelopmentRoutingOutcomeKind
{
    /// <summary>The request was routed, optionally naming one next capability.</summary>
    Routed,
    /// <summary>The flow must stop for an explicit human decision.</summary>
    HumanDecisionRequired,
    /// <summary>No supported development flow is available.</summary>
    FlowUnavailable,
}
