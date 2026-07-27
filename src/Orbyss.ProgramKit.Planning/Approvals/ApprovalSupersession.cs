using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Approvals;

/// <summary>Records explicit approval supersession without mutating the prior decision.</summary>
public sealed record ApprovalSupersession(
    ApprovalSupersessionState State,
    ArtifactReference? SupersededBy);
