using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>Records one approval condition and the evidence used to close it, when applicable.</summary>
public sealed record ApprovalCondition(
    string ConditionId,
    string Description,
    ApprovalConditionState State,
    ArtifactReference? ResolutionEvidence);
