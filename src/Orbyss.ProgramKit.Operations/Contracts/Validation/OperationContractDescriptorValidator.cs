using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.Operations.Contracts.Validation;

/// <summary>Validates one product-neutral operation descriptor.</summary>
public sealed class OperationContractDescriptorValidator :
    IProgramKitSemanticValidator<OperationContractDescriptor>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OperationContractDescriptor value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        Validate(value, "$", diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    internal static void Validate(
        OperationContractDescriptor value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        OperationsValidation.ValidateReference(
            value.OperationRevision,
            string.Concat(path, ".operationRevision"),
            diagnostics,
            "operation");
        OperationsValidation.ValidateReferenceSet(
            value.RequestContractRevisions,
            string.Concat(path, ".requestContractRevisions"),
            diagnostics,
            "schema");
        ValidateResults(value.ResultContracts, string.Concat(path, ".resultContracts"), diagnostics);
        OperationsValidation.ValidateReferenceSet(
            value.DiagnosticContractRevisions,
            string.Concat(path, ".diagnosticContractRevisions"),
            diagnostics,
            "schema");
        OperationsValidation.ValidateReferenceSet(
            value.ProgressContractRevisions,
            string.Concat(path, ".progressContractRevisions"),
            diagnostics,
            "schema");
        ValidateRelations(value.RelatedOperations, string.Concat(path, ".relatedOperations"), diagnostics);
        if (value.EffectContractRevision is not null)
        {
            OperationsValidation.ValidateReference(
                value.EffectContractRevision,
                string.Concat(path, ".effectContractRevision"),
                diagnostics);
        }

        if (value.AuthorityContractRevision is not null)
        {
            OperationsValidation.ValidateReference(
                value.AuthorityContractRevision,
                string.Concat(path, ".authorityContractRevision"),
                diagnostics);
        }

        ValidateEnum(value.ExpectedRevisionPolicy, string.Concat(path, ".expectedRevisionPolicy"), diagnostics);
        ValidateEnum(value.IdempotencyPolicy, string.Concat(path, ".idempotencyPolicy"), diagnostics);
        ValidateEnum(value.CancellationPolicy, string.Concat(path, ".cancellationPolicy"), diagnostics);
        ValidateEnum(value.ProgressPolicy, string.Concat(path, ".progressPolicy"), diagnostics);
        if (value.ProgressPolicy == OperationProgressPolicy.Unsupported &&
            !value.ProgressContractRevisions.IsDefaultOrEmpty)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidPolicyCombination,
                "Unsupported progress cannot declare progress contracts.",
                string.Concat(path, ".progressContractRevisions")));
        }
        else if (value.ProgressPolicy == OperationProgressPolicy.BoundedNonAuthoritative &&
                 value.ProgressContractRevisions.IsDefaultOrEmpty)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidPolicyCombination,
                "Bounded progress requires at least one exact progress contract.",
                string.Concat(path, ".progressContractRevisions")));
        }

        OperationsValidation.ValidateCompatibility(
            value.Compatibility,
            string.Concat(path, ".compatibility"),
            diagnostics);
        ValidateDeprecation(value, path, diagnostics);
    }

    private static void ValidateResults(
        ImmutableArray<OperationResultContract> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "At least one result contract is required.",
                path));
            return;
        }

        var contracts = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var itemPath = string.Concat(path, "[", index, "]");
            if (value is null)
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.MissingRequiredValue,
                    "A result contract cannot be null.",
                    itemPath));
                continue;
            }

            OperationsValidation.ValidateReference(
                value.ContractRevision,
                string.Concat(itemPath, ".contractRevision"),
                diagnostics,
                "schema");
            ValidateEnum(value.Disposition, string.Concat(itemPath, ".disposition"), diagnostics);
            if (!contracts.Add(OperationsValidation.ExactKey(value.ContractRevision)))
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.DuplicateRegistration,
                    "A result contract revision can be registered only once.",
                    itemPath));
            }
        }
    }

    private static void ValidateRelations(
        ImmutableArray<RelatedOperationContract> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "Related operations must be initialized.",
                path));
            return;
        }

        var relations = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            var itemPath = string.Concat(path, "[", index, "]");
            if (value is null)
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.MissingRequiredValue,
                    "A related operation cannot be null.",
                    itemPath));
                continue;
            }

            OperationsValidation.RequireIdentifier(
                value.RelationId,
                string.Concat(itemPath, ".relationId"),
                diagnostics);
            OperationsValidation.ValidateReference(
                value.OperationRevision,
                string.Concat(itemPath, ".operationRevision"),
                diagnostics,
                "operation");
            OperationsValidation.ValidateReference(
                value.RequestContractRevision,
                string.Concat(itemPath, ".requestContractRevision"),
                diagnostics,
                "schema");
            var key = string.Concat(
                value.RelationId.Value,
                "|",
                OperationsValidation.ExactKey(value.OperationRevision));
            if (!relations.Add(key))
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.DuplicateRegistration,
                    "A typed related-operation registration must be unique.",
                    itemPath));
            }
        }
    }

    private static void ValidateDeprecation(
        OperationContractDescriptor value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Deprecation is null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "Deprecation metadata is required.",
                string.Concat(path, ".deprecation")));
            return;
        }

        if (!value.Deprecation.IsDeprecated && value.Deprecation.ReplacedBy is not null)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidPolicyCombination,
                "A non-deprecated operation cannot declare a replacement.",
                string.Concat(path, ".deprecation.replacedBy")));
        }

        if (value.Deprecation.ReplacedBy is not null)
        {
            OperationsValidation.ValidateReference(
                value.Deprecation.ReplacedBy,
                string.Concat(path, ".deprecation.replacedBy"),
                diagnostics,
                "operation");
            if (value.Deprecation.ReplacedBy == value.OperationRevision)
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.InvalidPolicyCombination,
                    "An operation revision cannot replace itself.",
                    string.Concat(path, ".deprecation.replacedBy")));
            }
        }
    }

    private static void ValidateEnum<TEnum>(
        TEnum value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
        where TEnum : struct, Enum
    {
        if (!Enum.IsDefined(value))
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.InvalidEnumValue,
                "The enum value must be defined.",
                path));
        }
    }
}
