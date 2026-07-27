using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Fail-closed semantic validation for static-conformance dispositions.</summary>
public sealed class StaticConformanceDispositionValidator :
    IProgramKitSemanticValidator<StaticConformanceDisposition>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(StaticConformanceDisposition value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc700,
                "/",
                "A static-conformance disposition is required.");
            return diagnostics.ToResult();
        }

        diagnostics.Reference(value.SoftwareDesign, "/softwareDesign");
        ValidateAllocations(value.InvariantAllocations, diagnostics);
        if (!Enum.IsDefined(value.Disposition))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc701,
                "/disposition",
                "The static-conformance disposition is unsupported.");
        }

        var selections = ArchitectureValidation.OrEmpty(value.GateSelections);
        var linkedDesigns = ArchitectureValidation.OrEmpty(value.LinkedGateDesigns);
        var blockers = ArchitectureValidation.OrEmpty(value.Blockers);
        ValidateSelections(selections, diagnostics);
        ValidateReferences(linkedDesigns, "/linkedGateDesigns", diagnostics);
        RequireStatements(value.ResidualRisks, "/residualRisks", "residual risk", diagnostics);
        RequireStatements(value.NonStaticClaims, "/nonStaticClaims", "non-static claim", diagnostics);
        diagnostics.Required(value.Rationale, "/rationale", "Disposition rationale");
        if (value.DecisionSource is null)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc702,
                "/decisionSource",
                "An exact human-supplied disposition decision source is required.");
        }
        else
        {
            diagnostics.Reference(value.DecisionSource.Source, "/decisionSource/source");
            diagnostics.Required(
                value.DecisionSource.JsonPointer,
                "/decisionSource/jsonPointer",
                "Decision-source JSON pointer");
        }

        switch (value.Disposition)
        {
            case StaticConformanceDispositionKind.ReuseExisting:
                RequireCardinality(selections.Length > 0, "/gateSelections",
                    "reuse-existing requires at least one selected gate.", diagnostics);
                RequireNoEmptyAcceptance(value, diagnostics);
                RequireCardinality(blockers.Length == 0, "/blockers",
                    "reuse-existing cannot carry blockers.", diagnostics);
                break;
            case StaticConformanceDispositionKind.ExtendExisting:
                RequireCardinality(selections.Length > 0, "/gateSelections",
                    "extend-existing requires an existing selected gate.", diagnostics);
                RequireCardinality(linkedDesigns.Length > 0, "/linkedGateDesigns",
                    "extend-existing requires an exact linked gate design.", diagnostics);
                RequireNoEmptyAcceptance(value, diagnostics);
                RequireCardinality(blockers.Length == 0, "/blockers",
                    "extend-existing cannot carry blockers.", diagnostics);
                break;
            case StaticConformanceDispositionKind.CreateNew:
                RequireCardinality(linkedDesigns.Length > 0, "/linkedGateDesigns",
                    "create-new requires an exact linked gate design.", diagnostics);
                RequireNoEmptyAcceptance(value, diagnostics);
                RequireCardinality(blockers.Length == 0, "/blockers",
                    "create-new cannot carry blockers.", diagnostics);
                break;
            case StaticConformanceDispositionKind.NotJustified:
                RequireCardinality(selections.Length == 0, "/gateSelections",
                    "not-justified requires the exact empty gate selection.", diagnostics);
                RequireCardinality(linkedDesigns.Length == 0, "/linkedGateDesigns",
                    "not-justified cannot link a gate design.", diagnostics);
                RequireCardinality(blockers.Length == 0, "/blockers",
                    "not-justified cannot conceal unavailable-gate blockers.", diagnostics);
                diagnostics.Reference(
                    value.EmptySelectionAcceptance,
                    "/emptySelectionAcceptance");
                break;
            case StaticConformanceDispositionKind.BlockedUnavailable:
                RequireCardinality(blockers.Length > 0, "/blockers",
                    "blocked-unavailable requires at least one explicit blocker.", diagnostics);
                RequireStatements(blockers, "/blockers", "blocker", diagnostics);
                RequireNoEmptyAcceptance(value, diagnostics);
                break;
        }

        return diagnostics.ToResult();
    }

    private static void ValidateAllocations(
        ImmutableArray<StaticInvariantAllocation> values,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var allocations = ArchitectureValidation.OrEmpty(values);
        if (allocations.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc703,
                "/invariantAllocations",
                "At least one static invariant allocation is required.");
        }

        var identities = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < allocations.Length; index++)
        {
            var allocation = allocations[index];
            var path = $"/invariantAllocations/{index}";
            diagnostics.Identifier(allocation.Identity, $"{path}/identity");
            diagnostics.Required(allocation.Invariant, $"{path}/invariant", "Invariant");
            diagnostics.Required(allocation.Rationale, $"{path}/rationale", "Layer rationale");
            if (!Enum.IsDefined(allocation.Layer))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc704,
                    $"{path}/layer",
                    "The enforcement layer is unsupported.");
            }

            if (!identities.Add(allocation.Identity.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc705,
                    $"{path}/identity",
                    "Invariant allocation identities must be unique.");
            }
        }
    }

    private static void ValidateSelections(
        ImmutableArray<StaticConformanceGateSelection> selections,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var identities = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < selections.Length; index++)
        {
            var selection = selections[index];
            var path = $"/gateSelections/{index}";
            if (selection is null)
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc706,
                    path,
                    "A gate selection cannot be null.");
                continue;
            }

            diagnostics.Reference(selection.Gate, $"{path}/gate");
            diagnostics.Reference(selection.ActivationMatrix, $"{path}/activationMatrix");
            if (selection.Gate is not null &&
                !identities.Add(selection.Gate.Identity.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc707,
                    $"{path}/gate/identity",
                    "Selected gate identities must be unique and ordered once.");
            }
        }
    }

    private static void ValidateReferences(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        for (var index = 0; index < values.Length; index++)
        {
            diagnostics.Reference(values[index], $"{path}/{index}");
        }
    }

    private static void RequireStatements(
        ImmutableArray<string> values,
        string path,
        string description,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var statements = ArchitectureValidation.OrEmpty(values);
        if (statements.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc708,
                path,
                $"At least one {description} is required.");
        }

        for (var index = 0; index < statements.Length; index++)
        {
            diagnostics.Required(statements[index], $"{path}/{index}", description);
        }
    }

    private static void RequireNoEmptyAcceptance(
        StaticConformanceDisposition value,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.EmptySelectionAcceptance is not null)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc709,
                "/emptySelectionAcceptance",
                "Only not-justified may carry exact empty-selection acceptance.");
        }
    }

    private static void RequireCardinality(
        bool condition,
        string path,
        string message,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (!condition)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc710, path, message);
        }
    }
}
