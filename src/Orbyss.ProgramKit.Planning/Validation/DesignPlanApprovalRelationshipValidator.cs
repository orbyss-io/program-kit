using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Approvals;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>
/// Validates the relationship among a plan payload, externally verified exact plan/design
/// references, and a supplied human approval. This validator does not verify canonical bytes and
/// does not itself grant implementation authority.
/// </summary>
public sealed class DesignPlanApprovalRelationshipValidator
    : IDesignPlanApprovalRelationshipValidator
{
    private readonly IProgramKitSemanticValidator<ImplementationPlanDocument> _planValidator;
    private readonly IProgramKitSemanticValidator<DesignPlanApprovalRecord> _approvalValidator;

    /// <summary>Creates a relationship validator with explicit semantic dependencies.</summary>
    public DesignPlanApprovalRelationshipValidator(
        IProgramKitSemanticValidator<ImplementationPlanDocument> planValidator,
        IProgramKitSemanticValidator<DesignPlanApprovalRecord> approvalValidator)
    {
        ArgumentNullException.ThrowIfNull(planValidator);
        ArgumentNullException.ThrowIfNull(approvalValidator);

        _planValidator = planValidator;
        _approvalValidator = approvalValidator;
    }

    /// <summary>
    /// Validates approval eligibility after the caller has independently verified the supplied
    /// plan and design references against canonical artifact bytes.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ImplementationPlanDocument plan,
        ArtifactReference observedPlan,
        ArtifactReference observedDesign,
        DesignPlanApprovalRecord? suppliedApproval)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(observedPlan);
        ArgumentNullException.ThrowIfNull(observedDesign);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(_planValidator.Validate(plan).Diagnostics);
        PlanningValidation.ValidateReference(observedPlan, "$.planReference", diagnostics);
        PlanningValidation.ValidateReference(observedDesign, "$.designReference", diagnostics);
        if (plan.Design != observedDesign)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln301,
                "The observed design does not match the plan's exact design ID, version, and digest.",
                "$.design"));
        }

        if (plan.State != ImplementationPlanState.ReadyForHumanDecision)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln302,
                "Only a plan ready for human decision can be implementable.",
                "$.state"));
        }

        if (!plan.UnresolvedDecisions.IsDefault
            && plan.UnresolvedDecisions.Any(decision => decision is { BlocksImplementation: true }))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln303,
                "A blocking unresolved decision prevents implementation.",
                "$.unresolvedDecisions"));
        }

        if (suppliedApproval is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln304,
                "An exact human-supplied approval record is required.",
                "$.approval"));
        }
        else
        {
            diagnostics.AddRange(_approvalValidator.Validate(suppliedApproval).Diagnostics);
            if (suppliedApproval.Design != observedDesign)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln305,
                    "Approval does not bind the exact observed design.",
                    "$.approval.design"));
            }

            if (suppliedApproval.Plan != observedPlan)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln306,
                    "Approval does not bind the exact implementation plan.",
                    "$.approval.plan"));
            }

            if (suppliedApproval.Decision != DesignPlanApprovalDecision.Approved)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln307,
                    "Only an explicitly supplied approved decision permits implementation.",
                    "$.approval.decision"));
            }

            if (!suppliedApproval.Conditions.IsDefault
                && suppliedApproval.Conditions.Any(condition => condition is { State: ApprovalConditionState.Open }))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln308,
                    "An open approval condition prevents implementation.",
                    "$.approval.conditions"));
            }

            if (suppliedApproval.Supersession is not { State: ApprovalSupersessionState.Active })
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln309,
                    "A missing or superseded approval prevents implementation.",
                    "$.approval.supersession"));
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
