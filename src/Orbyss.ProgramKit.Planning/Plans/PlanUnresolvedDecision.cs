namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Records an unresolved human or external decision without silently choosing an answer.</summary>
public sealed record PlanUnresolvedDecision(
    string DecisionId,
    string Question,
    bool BlocksImplementation);
