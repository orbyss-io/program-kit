using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.Operations.Contracts.Validation;

/// <summary>Validates bounded non-authoritative progress carriage.</summary>
public sealed class OperationProgressDocumentValidator :
    IProgramKitSemanticValidator<OperationProgressDocument>
{
    private readonly OperationContractCatalog _catalog;

    /// <summary>Creates a validator over one already explicit catalog.</summary>
    public OperationProgressDocumentValidator(OperationContractCatalog catalog)
    {
        ArgumentNullException.ThrowIfNull(catalog);
        _catalog = catalog;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OperationProgressDocument value)
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
            value.ProgressContractRevision,
            "$.progressContractRevision",
            diagnostics,
            "schema");
        OperationsValidation.ValidateReference(
            value.ProgressDocumentRevision,
            "$.progressDocumentRevision",
            diagnostics);
        if (value.Sequence < 0)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidProgress,
                "Progress sequence cannot be negative.",
                "$.sequence"));
        }

        var descriptor = _catalog.Operations.FirstOrDefault(candidate =>
            candidate is not null &&
            candidate.OperationRevision == value.OperationRevision);
        if (descriptor is null ||
            descriptor.ProgressPolicy != OperationProgressPolicy.BoundedNonAuthoritative ||
            !descriptor.ProgressContractRevisions.Contains(
                value.ProgressContractRevision))
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidProgress,
                "Progress must resolve to an exact declared bounded progress contract.",
                "$.progressContractRevision"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
