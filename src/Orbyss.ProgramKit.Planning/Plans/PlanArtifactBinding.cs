using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Planning.Plans;

/// <summary>
/// One explicit human-approved binding whose exact bytes are fixed at approval
/// or selected under an exact compatibility policy during execution.
/// </summary>
public sealed record PlanArtifactBinding(
    PlanArtifactBindingResolutionMode ResolutionMode,
    ArtifactReference? ApprovedArtifact,
    ProgramKitIdentifier? ApprovedIdentity,
    SemanticVersionRange? AcceptedVersions,
    ArtifactReference? CompatibilityPolicy)
{
    /// <summary>Creates a binding to exact human-approved bytes.</summary>
    public static PlanArtifactBinding ApprovalFixed(
        ArtifactReference approvedArtifact)
    {
        ArgumentNullException.ThrowIfNull(approvedArtifact);
        return new PlanArtifactBinding(
            PlanArtifactBindingResolutionMode.ApprovalFixed,
            approvedArtifact,
            null,
            null,
            null);
    }

    /// <summary>Creates a binding resolved to exact compatible bytes at execution.</summary>
    public static PlanArtifactBinding ExecutionResolved(
        ProgramKitIdentifier approvedIdentity,
        SemanticVersionRange acceptedVersions,
        ArtifactReference compatibilityPolicy)
    {
        ArgumentNullException.ThrowIfNull(compatibilityPolicy);
        return new PlanArtifactBinding(
            PlanArtifactBindingResolutionMode.ExecutionResolved,
            null,
            approvedIdentity,
            acceptedVersions,
            compatibilityPolicy);
    }
}
