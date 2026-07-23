namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>Identifies the state of one explicitly supplied approval condition.</summary>
public enum ApprovalConditionState
{
    /// <summary>The condition remains unresolved.</summary>
    Open,
    /// <summary>The condition has been satisfied with evidence.</summary>
    Satisfied,
    /// <summary>The condition was explicitly waived with evidence.</summary>
    Waived,
}
