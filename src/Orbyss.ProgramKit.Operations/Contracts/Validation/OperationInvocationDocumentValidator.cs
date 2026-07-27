using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.Operations.Contracts.Validation;

/// <summary>Validates canonical invocation carriage against an explicit catalog.</summary>
public sealed class OperationInvocationDocumentValidator :
    IProgramKitSemanticValidator<OperationInvocationDocument>
{
    private readonly OperationContractCatalog _catalog;

    /// <summary>Creates a validator over one already explicit catalog.</summary>
    public OperationInvocationDocumentValidator(OperationContractCatalog catalog)
    {
        ArgumentNullException.ThrowIfNull(catalog);
        _catalog = catalog;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OperationInvocationDocument value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        OperationsValidation.RequireText(value.InvocationId, "$.invocationId", diagnostics);
        OperationsValidation.RequireText(value.CorrelationId, "$.correlationId", diagnostics);
        OperationsValidation.ValidateReference(
            value.OperationRevision,
            "$.operationRevision",
            diagnostics,
            "operation");
        OperationsValidation.ValidateReference(
            value.RequestContractRevision,
            "$.requestContractRevision",
            diagnostics,
            "schema");
        OperationsValidation.ValidateReference(
            value.RequestDocumentRevision,
            "$.requestDocumentRevision",
            diagnostics);
        if (string.Equals(value.InvocationId, value.CausationId, StringComparison.Ordinal))
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "An invocation cannot cause itself.",
                "$.causationId"));
        }

        var descriptor = ResolveDescriptor(value.OperationRevision);
        if (descriptor is null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "The invocation operation must resolve exactly in the explicit catalog.",
                "$.operationRevision"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (!descriptor.RequestContractRevisions.Contains(value.RequestContractRevision))
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "The invocation request contract is not declared by the operation.",
                "$.requestContractRevision"));
        }

        ValidateExpectedRevision(value, descriptor, diagnostics);
        ValidateIdempotency(value, descriptor, diagnostics);
        ValidateCancellation(value, descriptor, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private OperationContractDescriptor? ResolveDescriptor(ArtifactReference revision) =>
        _catalog.Operations.FirstOrDefault(candidate =>
            candidate is not null && candidate.OperationRevision == revision);

    private static void ValidateExpectedRevision(
        OperationInvocationDocument value,
        OperationContractDescriptor descriptor,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (descriptor.ExpectedRevisionPolicy == OperationExpectedRevisionPolicy.Unsupported &&
            value.ExpectedRevision is not null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "This operation does not accept an expected revision.",
                "$.expectedRevision"));
        }
        else if (descriptor.ExpectedRevisionPolicy == OperationExpectedRevisionPolicy.Required &&
                 value.ExpectedRevision is null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "This operation requires an expected revision.",
                "$.expectedRevision"));
        }

        if (value.ExpectedRevision is not null)
        {
            OperationsValidation.ValidateReference(
                value.ExpectedRevision,
                "$.expectedRevision",
                diagnostics);
        }
    }

    private static void ValidateIdempotency(
        OperationInvocationDocument value,
        OperationContractDescriptor descriptor,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (descriptor.IdempotencyPolicy == OperationIdempotencyPolicy.Unsupported &&
            value.IdempotencyKey is not null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "This operation does not accept an idempotency key.",
                "$.idempotencyKey"));
        }
        else if (descriptor.IdempotencyPolicy == OperationIdempotencyPolicy.Required &&
                 string.IsNullOrWhiteSpace(value.IdempotencyKey))
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "This operation requires an idempotency key.",
                "$.idempotencyKey"));
        }
    }

    private static void ValidateCancellation(
        OperationInvocationDocument value,
        OperationContractDescriptor descriptor,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (descriptor.CancellationPolicy == OperationCancellationPolicy.Unsupported &&
            value.CancellationSignalId is not null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidInvocation,
                "This operation does not accept a cancellation signal.",
                "$.cancellationSignalId"));
        }
        else if (value.CancellationSignalId is not null)
        {
            OperationsValidation.RequireText(
                value.CancellationSignalId,
                "$.cancellationSignalId",
                diagnostics);
        }
    }
}
