namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Identifies the lifecycle state of an implementation plan without implying human approval.</summary>
public enum ImplementationPlanState
{
    /// <summary>The plan remains under construction.</summary>
    Draft,
    /// <summary>The plan is complete enough for an explicit human decision.</summary>
    ReadyForHumanDecision,
    /// <summary>A later plan revision has replaced this plan.</summary>
    Superseded,
}
