namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>Determines when the exact bytes for one plan binding are selected.</summary>
public enum PlanArtifactBindingResolutionMode
{
    /// <summary>The human approves the exact artifact identity, version, and digest.</summary>
    ApprovalFixed,

    /// <summary>
    /// The human approves identity and compatibility policy; execution records
    /// the exact compatible selected artifact.
    /// </summary>
    ExecutionResolved,
}
