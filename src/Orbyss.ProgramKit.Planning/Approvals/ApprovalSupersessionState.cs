namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>Identifies whether an approval record remains active.</summary>
public enum ApprovalSupersessionState
{
    /// <summary>The approval remains the active decision for its exact inputs.</summary>
    Active,
    /// <summary>A later approval record supersedes this record.</summary>
    Superseded,
}
