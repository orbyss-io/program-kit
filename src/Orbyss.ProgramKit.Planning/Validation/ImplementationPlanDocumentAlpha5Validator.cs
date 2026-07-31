using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;

namespace Orbyss.ProgramKit.Planning.Validation;

/// <summary>
/// Validates Planning alpha.5 without converting execution-resolved bindings
/// into invented exact artifact references.
/// </summary>
public sealed class ImplementationPlanDocumentAlpha5Validator :
    IProgramKitSemanticValidator<ImplementationPlanDocumentAlpha5>
{
    private static readonly SemanticVersion DesignVersion =
        new("0.1.0-alpha.3");
    private static readonly SemanticVersion DispositionVersion =
        new("0.1.0-alpha.2");
    private readonly IProgramKitSemanticValidator<ImplementationPlanDocument>
        versionTwoValidator;

    /// <summary>Initializes alpha.5 validation over existing plan semantics.</summary>
    public ImplementationPlanDocumentAlpha5Validator(
        IProgramKitSemanticValidator<ImplementationPlanDocument>
            versionTwoValidator)
    {
        this.versionTwoValidator = versionTwoValidator ??
            throw new ArgumentNullException(nameof(versionTwoValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        ImplementationPlanDocumentAlpha5 value)
    {
        if (value is null)
        {
            return ProgramKitValidationResult.From(
            [
                PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln142,
                    "A Planning 0.1.0-alpha.5 implementation plan is required.",
                    "$"),
            ]);
        }

        var legacy = ImplementationPlanAlpha3ToAlpha4Migration.ToAlpha3Shape(
            ImplementationPlanAlpha4ToAlpha5Migration.ToAlpha4Shape(value));
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(
            ImplementationPlanDocumentV3Validator.ValidateVersioned(
                ImplementationPlanV3ToAlpha3Migration.ToLegacyShape(legacy),
                versionTwoValidator,
                DispositionVersion,
                "0.1.0-alpha.5",
                validateLegacyExactUnitBindings: false).Diagnostics);

        if (!string.Equals(
                value.Schema,
                ImplementationPlanDocumentAlpha5.SchemaUri,
                StringComparison.Ordinal))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln001,
                "Implementation Plan 0.1.0-alpha.5 requires its exact canonical $schema URI.",
                "$.$schema"));
        }

        if (!string.Equals(
                value.Design.Identity.Kind,
                "design",
                StringComparison.Ordinal) ||
            value.Design.Version != DesignVersion)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln143,
                "Planning 0.1.0-alpha.5 requires an exact design artifact at version 0.1.0-alpha.3.",
                "$.design"));
        }

        var units = value.WorkUnits.IsDefault
            ? ImmutableArray<PlanWorkUnitAlpha5>.Empty
            : value.WorkUnits;
        for (var index = 0; index < units.Length; index++)
        {
            ValidateUnitBindings(
                value.StaticConformanceState,
                units[index],
                index,
                diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateUnitBindings(
        StaticConformancePlanState state,
        PlanWorkUnitAlpha5 unit,
        int index,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var path = $"$.workUnits[{index}]";
        if (state == StaticConformancePlanState.AcceptedEmpty)
        {
            if (unit.ActivationMatrix is not null ||
                unit.VerificationProfile is not null)
            {
                diagnostics.Add(PlanningValidation.Error(
                    PlanningDiagnosticIds.Pkpln149,
                    "Accepted-empty work units cannot carry artifact bindings.",
                    path));
            }

            return;
        }

        ValidateBinding(
            unit.ActivationMatrix,
            "activation-matrix",
            $"{path}.activationMatrix",
            diagnostics);
        ValidateBinding(
            unit.VerificationProfile,
            "profile",
            $"{path}.verificationProfile",
            diagnostics);
    }

    private static void ValidateBinding(
        PlanArtifactBinding? binding,
        string expectedKind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (binding is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln149,
                "Every gated work unit requires an explicit artifact binding.",
                path));
            return;
        }

        if (!Enum.IsDefined(binding.ResolutionMode))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln149,
                "Artifact binding resolution mode must be defined.",
                $"{path}.resolutionMode"));
            return;
        }

        if (binding.ResolutionMode ==
            PlanArtifactBindingResolutionMode.ApprovalFixed)
        {
            ValidateApprovalFixed(binding, expectedKind, path, diagnostics);
            return;
        }

        ValidateExecutionResolved(binding, expectedKind, path, diagnostics);
    }

    private static void ValidateApprovalFixed(
        PlanArtifactBinding binding,
        string expectedKind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (binding.ApprovedArtifact is null ||
            binding.ApprovedIdentity is not null ||
            binding.AcceptedVersions is not null ||
            binding.CompatibilityPolicy is not null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln149,
                "An approval-fixed binding must contain only one exact approved artifact.",
                path));
            return;
        }

        PlanningValidation.ValidateReference(
            binding.ApprovedArtifact,
            $"{path}.approvedArtifact",
            diagnostics);
        PlanningValidation.RequireReferenceKind(
            binding.ApprovedArtifact,
            expectedKind,
            $"{path}.approvedArtifact",
            diagnostics,
            PlanningDiagnosticIds.Pkpln147);
    }

    private static void ValidateExecutionResolved(
        PlanArtifactBinding binding,
        string expectedKind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (binding.ApprovedArtifact is not null ||
            binding.ApprovedIdentity is null ||
            binding.AcceptedVersions is null ||
            binding.CompatibilityPolicy is null)
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln150,
                "An execution-resolved binding requires approved identity, accepted versions, and exact compatibility policy.",
                path));
            return;
        }

        var approvedIdentity = binding.ApprovedIdentity.Value;
        diagnostics.AddRange(ProgramKitIdentifier.Validate(
            approvedIdentity.Value,
            $"{path}.approvedIdentity").Diagnostics);
        if (!string.Equals(
                approvedIdentity.Kind,
                expectedKind,
                StringComparison.Ordinal))
        {
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln147,
                string.Concat(
                    "The approved identity must have kind '",
                    expectedKind,
                    "'."),
                $"{path}.approvedIdentity"));
        }

        diagnostics.AddRange(SemanticVersionRange.Validate(
            binding.AcceptedVersions.Value.Value,
            $"{path}.acceptedVersions").Diagnostics);
        PlanningValidation.ValidateReference(
            binding.CompatibilityPolicy,
            $"{path}.compatibilityPolicy",
            diagnostics);
    }
}
