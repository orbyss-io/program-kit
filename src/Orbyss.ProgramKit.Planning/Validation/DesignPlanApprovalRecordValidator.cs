using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Approvals;
using Orbyss.ProgramKit.Planning.Diagnostics;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>Validates a human-supplied design/plan approval record without originating a decision.</summary>
public sealed class DesignPlanApprovalRecordValidator :
    IArtifactEnvelopeSemanticValidator<DesignPlanApprovalRecord>
{
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates an approval validator with explicit envelope validation.</summary>
    public DesignPlanApprovalRecordValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(envelopeValidator);
        _envelopeValidator = envelopeValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(DesignPlanApprovalRecord value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        PlanningValidation.ValidateReference(value.Design, "$.design", diagnostics);
        PlanningValidation.ValidateReference(value.Plan, "$.plan", diagnostics);
        PlanningValidation.RequireReferenceKind(value.Design, "design", "$.design", diagnostics);
        PlanningValidation.RequireReferenceKind(value.Plan, "plan", "$.plan", diagnostics);
        PlanningValidation.RequireText(value.AcceptedScope, "$.acceptedScope", diagnostics);
        ValidatePrincipal(value.ApprovingPrincipal, diagnostics);
        ValidateAuthority(value.Authority, diagnostics);
        ValidateDecisionEvidence(value.DecisionEvidence, diagnostics);
        PlanningValidation.RequireText(value.CorrelationId, "$.correlationId", diagnostics);
        if (!Enum.IsDefined(value.Decision))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln216,
                "Approval decision must be a defined value.",
                "$.decision"));
        }

        if (value.DecisionTime == default)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln201,
                "A decision time supplied by the human-session boundary is required.",
                "$.decisionTime"));
        }

        ValidateConditions(value.Conditions, diagnostics);
        ValidateSupersession(value, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped approval and rejects exact payload references,
    /// including <c>supersededBy</c>, back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<DesignPlanApprovalRecord> envelope)
    {
        var diagnostics = PlanningEnvelopeValidation.ValidateEnvelope(
            envelope,
            this,
            _envelopeValidator);
        if (!PlanningEnvelopeValidation.TryCreateSelfReference(
                envelope,
                out var selfReference) ||
            envelope.Document is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Design,
            "/document/design",
            diagnostics);
        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Plan,
            "/document/plan",
            diagnostics);
        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Authority?.Source,
            "/document/authority/source",
            diagnostics);
        for (var index = 0; index < envelope.Document.Conditions.Length; index++)
        {
            PlanningEnvelopeValidation.Reject(
                selfReference,
                envelope.Document.Conditions[index]?.ResolutionEvidence,
                $"/document/conditions/{index}/resolutionEvidence",
                diagnostics);
        }

        PlanningEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Supersession?.SupersededBy,
            "/document/supersession/supersededBy",
            diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidatePrincipal(
        PrincipalReference? value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln202,
                "An approving principal supplied by the human session is required.",
                "$.approvingPrincipal"));
            return;
        }

        PlanningValidation.RequireText(value.Kind, "$.approvingPrincipal.kind", diagnostics);
        PlanningValidation.RequireText(value.Provider, "$.approvingPrincipal.provider", diagnostics);
        PlanningValidation.RequireText(value.Identifier, "$.approvingPrincipal.identifier", diagnostics);
        PlanningValidation.RequireText(value.Role, "$.approvingPrincipal.role", diagnostics);
    }

    private static void ValidateAuthority(
        AuthorityReference? value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln203,
                "A separate authority reference supplied by the human session is required.",
                "$.authority"));
            return;
        }

        PlanningValidation.RequireText(value.Kind, "$.authority.kind", diagnostics);
        PlanningValidation.ValidateReference(value.Source, "$.authority.source", diagnostics);
        PlanningValidation.RequireText(value.JsonPointer, "$.authority.jsonPointer", diagnostics);
        if (!string.IsNullOrWhiteSpace(value.JsonPointer)
            && value.JsonPointer[0] != '/')
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln204,
                "An authority JSON Pointer must be absolute.",
                "$.authority.jsonPointer"));
        }

        PlanningValidation.RequireIdentifier(value.OwnerId, "$.authority.ownerId", diagnostics);
    }

    private static void ValidateDecisionEvidence(
        ImmutableArray<HumanDecisionEvidence> values,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln205,
                "At least one human-decision evidence reference is required.",
                "$.decisionEvidence"));
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var path = $"$.decisionEvidence[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln206, "Decision evidence cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(value.Kind, $"{path}.kind", diagnostics);
            PlanningValidation.RequireText(value.Provider, $"{path}.provider", diagnostics);
            PlanningValidation.RequireText(value.ReferenceId, $"{path}.referenceId", diagnostics);
            if (value.Digest is { } digest && string.IsNullOrWhiteSpace(digest.Value))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln207,
                    "A supplied evidence digest must be an exact SHA-256 digest.",
                    $"{path}.digest"));
            }
        }
    }

    private static void ValidateConditions(
        ImmutableArray<ApprovalCondition> values,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln208,
                "Approval conditions must be initialized.",
                "$.conditions"));
            return;
        }

        var ids = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var path = $"$.conditions[{index}]";
            if (value is null)
            {
                diagnostics.Add(PlanningValidation.Error(PlanningDiagnosticIds.Pkpln209, "An approval condition cannot be null.", path));
                continue;
            }

            PlanningValidation.RequireText(value.ConditionId, $"{path}.conditionId", diagnostics);
            PlanningValidation.RequireText(value.Description, $"{path}.description", diagnostics);
            if (!Enum.IsDefined(value.State))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln217,
                    "Approval-condition state must be a defined value.",
                    $"{path}.state"));
            }

            if (!string.IsNullOrWhiteSpace(value.ConditionId) && !ids.Add(value.ConditionId))
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln210,
                    $"Approval condition '{value.ConditionId}' occurs more than once.",
                    $"{path}.conditionId"));
            }

            if (value.State == ApprovalConditionState.Open && value.ResolutionEvidence is not null)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln211,
                    "An open condition cannot carry resolution evidence.",
                    $"{path}.resolutionEvidence"));
            }
            else if (value.State != ApprovalConditionState.Open && value.ResolutionEvidence is null)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln212,
                    "A satisfied or waived condition requires exact resolution evidence.",
                    $"{path}.resolutionEvidence"));
            }
            else if (value.ResolutionEvidence is not null)
            {
                PlanningValidation.ValidateReference(
                    value.ResolutionEvidence,
                    $"{path}.resolutionEvidence",
                    diagnostics);
            }
        }
    }

    private static void ValidateSupersession(
        DesignPlanApprovalRecord approval,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (approval.Supersession is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln213,
                "Explicit supersession state is required.",
                "$.supersession"));
            return;
        }

        if (!Enum.IsDefined(approval.Supersession.State))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln218,
                "Approval supersession state must be a defined value.",
                "$.supersession.state"));
            return;
        }

        if (approval.Supersession.State == ApprovalSupersessionState.Active
            && approval.Supersession.SupersededBy is not null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln214,
                "An active approval cannot name a superseding record.",
                "$.supersession.supersededBy"));
        }
        else if (approval.Supersession.State == ApprovalSupersessionState.Superseded)
        {
            if (approval.Supersession.SupersededBy is null)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln215,
                    "A superseded approval must name its exact successor.",
                    "$.supersession.supersededBy"));
            }
            else
            {
                PlanningValidation.ValidateReference(
                    approval.Supersession.SupersededBy,
                    "$.supersession.supersededBy",
                    diagnostics);
                PlanningValidation.RequireReferenceKind(
                    approval.Supersession.SupersededBy,
                    "approval",
                    "$.supersession.supersededBy",
                    diagnostics);
            }
        }
    }
}
