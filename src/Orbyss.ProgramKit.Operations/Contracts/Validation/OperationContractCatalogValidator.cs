using Orbyss.ProgramKit.Operations.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.Operations.Contracts.Validation;

/// <summary>Validates duplicate-free explicit catalog closure.</summary>
public sealed class OperationContractCatalogValidator :
    IProgramKitSemanticValidator<OperationContractCatalog>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OperationContractCatalog value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value.Operations.IsDefaultOrEmpty)
        {
            diagnostics.Add(OperationsValidation.Error(
                OperationsDiagnosticIds.MissingRequiredValue,
                "At least one explicit operation descriptor is required.",
                "$.operations"));
            return ProgramKitValidationResult.From(diagnostics);
        }

        var exact = new Dictionary<string, OperationContractDescriptor>(StringComparer.Ordinal);
        var stable = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.Operations.Length; index++)
        {
            var descriptor = value.Operations[index];
            var path = string.Concat("$.operations[", index, "]");
            if (descriptor is null)
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.MissingRequiredValue,
                    "An operation descriptor cannot be null.",
                    path));
                continue;
            }

            OperationContractDescriptorValidator.Validate(descriptor, path, diagnostics);
            var exactKey = OperationsValidation.ExactKey(descriptor.OperationRevision);
            if (!exact.TryAdd(exactKey, descriptor))
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.DuplicateRegistration,
                    "An exact operation revision can be registered only once.",
                    string.Concat(path, ".operationRevision")));
            }

            if (!stable.Add(descriptor.OperationRevision.Identity.Value))
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.ConflictingRegistration,
                    "A finite catalog cannot register competing revisions of one operation identity.",
                    string.Concat(path, ".operationRevision.identity")));
            }
        }

        ValidateClosure(value.Operations, exact, diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    private static void ValidateClosure(
        ImmutableArray<OperationContractDescriptor> descriptors,
        Dictionary<string, OperationContractDescriptor> exact,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        for (var descriptorIndex = 0; descriptorIndex < descriptors.Length; descriptorIndex++)
        {
            var descriptor = descriptors[descriptorIndex];
            if (descriptor is null || descriptor.RelatedOperations.IsDefault)
            {
                continue;
            }

            for (var relationIndex = 0;
                 relationIndex < descriptor.RelatedOperations.Length;
                 relationIndex++)
            {
                var relation = descriptor.RelatedOperations[relationIndex];
                if (relation is null)
                {
                    continue;
                }

                var path = string.Concat(
                    "$.operations[",
                    descriptorIndex,
                    "].relatedOperations[",
                    relationIndex,
                    "]");
                if (!exact.TryGetValue(
                        OperationsValidation.ExactKey(relation.OperationRevision),
                        out var target))
                {
                    diagnostics.Add(OperationsValidation.Error(
                        OperationsDiagnosticIds.CatalogClosureFailure,
                        "A related operation must resolve exactly inside the finite catalog.",
                        string.Concat(path, ".operationRevision")));
                    continue;
                }

                if (!target.RequestContractRevisions.Contains(
                        relation.RequestContractRevision))
                {
                    diagnostics.Add(OperationsValidation.Error(
                        OperationsDiagnosticIds.CatalogClosureFailure,
                        "A related operation request contract must be declared by its target.",
                        string.Concat(path, ".requestContractRevision")));
                }
            }

            if (descriptor.Deprecation?.ReplacedBy is not null &&
                !exact.ContainsKey(
                    OperationsValidation.ExactKey(descriptor.Deprecation.ReplacedBy)))
            {
                diagnostics.Add(OperationsValidation.Error(
                    OperationsDiagnosticIds.CatalogClosureFailure,
                    "A replacement operation must resolve exactly inside the finite catalog.",
                    string.Concat(
                        "$.operations[",
                        descriptorIndex,
                        "].deprecation.replacedBy")));
            }
        }
    }
}
