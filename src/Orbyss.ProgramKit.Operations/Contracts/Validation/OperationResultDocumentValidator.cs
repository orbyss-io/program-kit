using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.Operations.Contracts.Validation;

/// <summary>Validates result carriage without interpreting domain-owned payloads.</summary>
public sealed class OperationResultDocumentValidator :
    IProgramKitSemanticValidator<OperationResultDocument>
{
    private readonly OperationContractCatalog _catalog;

    /// <summary>Creates a validator over one already explicit catalog.</summary>
    public OperationResultDocumentValidator(OperationContractCatalog catalog)
    {
        ArgumentNullException.ThrowIfNull(catalog);
        _catalog = catalog;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OperationResultDocument value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        OperationsValidation.RequireText(value.InvocationId, "$.invocationId", diagnostics);
        OperationsValidation.ValidateReference(
            value.OperationRevision,
            "$.operationRevision",
            diagnostics,
            "operation");
        OperationsValidation.ValidateReference(
            value.ResultContractRevision,
            "$.resultContractRevision",
            diagnostics,
            "schema");
        OperationsValidation.ValidateReference(
            value.ResultDocumentRevision,
            "$.resultDocumentRevision",
            diagnostics);
        if (!Enum.IsDefined(value.Disposition))
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidEnumValue,
                "The result disposition must be defined.",
                "$.disposition"));
        }

        var descriptor = _catalog.Operations.FirstOrDefault(candidate =>
            candidate is not null &&
            candidate.OperationRevision == value.OperationRevision);
        if (descriptor is null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidResult,
                "The result operation must resolve exactly in the explicit catalog.",
                "$.operationRevision"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        var resultContract = descriptor.ResultContracts.FirstOrDefault(candidate =>
            candidate is not null &&
            candidate.ContractRevision == value.ResultContractRevision);
        if (resultContract is null || resultContract.Disposition != value.Disposition)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidResult,
                "The exact result contract and disposition must match the descriptor.",
                "$.resultContractRevision"));
        }

        ValidateDiagnostics(value.Diagnostics, descriptor, diagnostics);
        ValidateRelatedOperation(value, descriptor, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateDiagnostics(
        ImmutableArray<OperationDiagnosticDocument> values,
        OperationContractDescriptor descriptor,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "Diagnostic documents must be initialized.",
                "$.diagnostics"));
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var path = string.Concat("$.diagnostics[", index, "]");
            if (value is null)
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.MissingRequiredValue,
                    "A diagnostic document cannot be null.",
                    path));
                continue;
            }

            OperationsValidation.ValidateReference(
                value.ContractRevision,
                string.Concat(path, ".contractRevision"),
                diagnostics,
                "schema");
            OperationsValidation.ValidateReference(
                value.DocumentRevision,
                string.Concat(path, ".documentRevision"),
                diagnostics);
            if (!descriptor.DiagnosticContractRevisions.Contains(value.ContractRevision))
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.InvalidResult,
                    "A diagnostic contract must be declared by the operation.",
                    string.Concat(path, ".contractRevision")));
            }
        }
    }

    private static void ValidateRelatedOperation(
        OperationResultDocument value,
        OperationContractDescriptor descriptor,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Disposition == OperationResultDisposition.Terminal &&
            value.RelatedOperationRevision is not null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidResult,
                "A terminal result cannot select a related operation.",
                "$.relatedOperationRevision"));
        }
        else if (value.Disposition == OperationResultDisposition.AdditionalInputRequired)
        {
            if (value.RelatedOperationRevision is null ||
                !descriptor.RelatedOperations.Any(relation =>
                    relation is not null &&
                    relation.OperationRevision == value.RelatedOperationRevision))
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.InvalidResult,
                    "Additional input requires one exact related operation declared by the descriptor.",
                    "$.relatedOperationRevision"));
            }
        }

        if (value.RelatedOperationRevision is not null)
        {
            OperationsValidation.ValidateReference(
                value.RelatedOperationRevision,
                "$.relatedOperationRevision",
                diagnostics,
                "operation");
        }
    }
}
