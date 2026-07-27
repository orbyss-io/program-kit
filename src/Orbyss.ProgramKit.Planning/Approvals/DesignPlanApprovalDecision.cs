namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>Identifies the only decisions accepted by the design/plan approval contract.</summary>
public enum DesignPlanApprovalDecision
{
    /// <summary>The human approved the exact design and plan.</summary>
    Approved,
    /// <summary>The human rejected the exact design and plan.</summary>
    Rejected,
    /// <summary>The human requires changes before approval.</summary>
    ChangesRequired,
}
