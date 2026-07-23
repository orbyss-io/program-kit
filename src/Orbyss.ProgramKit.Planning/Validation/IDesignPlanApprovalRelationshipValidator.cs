using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Approvals;
using Orbyss.ProgramKit.Planning.Plans;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>
/// Validates whether an exact, externally verified design and plan are
/// covered by the supplied human approval record.
/// </summary>
public interface IDesignPlanApprovalRelationshipValidator
{
    /// <summary>
    /// Validates approval eligibility without granting implementation
    /// authority or verifying canonical artifact bytes.
    /// </summary>
    ProgramKitValidationResult Validate(
        ImplementationPlanDocument plan,
        ArtifactReference observedPlan,
        ArtifactReference observedDesign,
        DesignPlanApprovalRecord? suppliedApproval);
}
