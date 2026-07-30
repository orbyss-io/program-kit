using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;

/// <summary>Pure structural validation for selection lock 0.1.0-alpha.1.</summary>
public sealed class CSharpBuildGateSelectionLockAlpha1Validator :
    IProgramKitSemanticValidator<CSharpBuildGateSelectionLockDocumentAlpha1>
{
    private static readonly SemanticVersion Version =
        new("0.1.0-alpha.1");

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(
        CSharpBuildGateSelectionLockDocumentAlpha1 value)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                CSharpBuildGateDiagnosticIds.Pkcg011,
                "$",
                "A C# build-gate selection lock is required.");
            return ProgramKitValidationResult.From(diagnostics);
        }

        diagnostics.Require(
            value.Version == Version &&
            value.Disposition is not null &&
            value.GateDefinition is not null &&
            value.RuleCatalog is not null &&
            value.ActivationMatrix is not null &&
            value.SuppressionLedger is not null,
            CSharpBuildGateDiagnosticIds.Pkcg011,
            "$",
            "Selection lock 0.1.0-alpha.1 requires every exact governing artifact.");
        ValidateReferences(
            value.AnalyzerComponents,
            "$.analyzerComponents",
            diagnostics);
        ValidateReferences(value.Recipes, "$.recipes", diagnostics, false);
        ValidateReferences(
            value.OperationRevisions,
            "$.operationRevisions",
            diagnostics);
        ValidateInventory(
            value.ProjectInventory,
            "$.projectInventory",
            diagnostics);
        ValidateInventory(
            value.PhysicalSourceInventory,
            "$.physicalSourceInventory",
            diagnostics);
        ValidateInventory(
            value.GeneratedSourceInventory,
            "$.generatedSourceInventory",
            diagnostics,
            false);
        ValidateInventory(
            value.ReferenceInventory,
            "$.referenceInventory",
            diagnostics);
        ValidateInventory(
            value.AdditionalFileInventory,
            "$.additionalFileInventory",
            diagnostics,
            false);
        ValidateInventory(
            value.AnalyzerConfigurationInventory,
            "$.analyzerConfigurationInventory",
            diagnostics,
            false);
        CSharpBuildGateValidation.ValidateStableUnique(
            value.ExpectedReceipts,
            CSharpBuildGateOrdering.ExpectedReceiptKey,
            "$.expectedReceipts",
            diagnostics);
        var physical = value.PhysicalSourceInventory
            .Select(static item => item.RepositoryRelativePath)
            .ToHashSet(StringComparer.Ordinal);
        diagnostics.Require(
            !value.GeneratedSourceInventory.Any(item =>
                physical.Contains(item.RepositoryRelativePath)),
            CSharpBuildGateDiagnosticIds.Pkcg011,
            "$.generatedSourceInventory",
            "Physical and generated source inventories cannot overlap.");
        diagnostics.Require(
            !string.IsNullOrWhiteSpace(value.TargetFramework),
            CSharpBuildGateDiagnosticIds.Pkcg011,
            "$.targetFramework",
            "An exact target framework is required.");
        return diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateReferences(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        bool requireOne = true) =>
        CSharpBuildGateValidation.ValidateStableUnique(
            values,
            CSharpBuildGateOrdering.ArtifactReferenceKey,
            path,
            diagnostics,
            requireOne);

    private static void ValidateInventory(
        ImmutableArray<CSharpGateLockedContent> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        bool requireOne = true)
    {
        CSharpBuildGateValidation.ValidateStableUnique(
            values,
            CSharpBuildGateOrdering.InventoryKey,
            path,
            diagnostics,
            requireOne);
        if (!values.IsDefault)
        {
            diagnostics.Require(
                values.All(static item =>
                    CSharpBuildGateValidation.IsExactRepositoryPath(
                        item.RepositoryRelativePath)),
                CSharpBuildGateDiagnosticIds.Pkcg011,
                path,
                "Selection locks contain exact paths only.");
        }
    }
}
