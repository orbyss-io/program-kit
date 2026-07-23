using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture;

/// <summary>Validates the ten required operation semantic dimensions.</summary>
public sealed class OperationDefinitionValidator :
    IProgramKitSemanticValidator<OperationDefinition>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(OperationDefinition value)
    {
        var diagnostics = new ArchitectureDiagnosticBag();
        if (value is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc100, "/", "An operation definition is required.");
            return diagnostics.ToResult();
        }

        ValidateInto(value, "/", diagnostics);
        return diagnostics.ToResult();
    }

    internal static void ValidateInto(
        OperationDefinition operation,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        diagnostics.Identifier(operation.Identity, $"{path}identity");
        diagnostics.Identifier(operation.OwnerDomainId, $"{path}ownerDomainId");
        diagnostics.Required(operation.Purpose, $"{path}purpose", "Operation purpose");

        ValidateInput(operation.Input, $"{path}input", diagnostics);
        ValidateOutput(operation.Output, $"{path}output", diagnostics);
        ValidateSideEffects(operation.SideEffects, $"{path}sideEffects", diagnostics);
        ValidateAuthority(operation.Authority, $"{path}authority", diagnostics);
        ValidateFailures(operation.Failures, $"{path}failures", diagnostics);
        ValidateCancellation(operation.Cancellation, $"{path}cancellation", diagnostics);
        ValidateIdempotency(operation.Idempotency, $"{path}idempotency", diagnostics);
        ValidateCompatibility(operation.Compatibility, $"{path}compatibility", diagnostics);
        ValidateObservability(operation.Observability, $"{path}observability", diagnostics);
        ValidateResources(operation.ResourceOwnership, $"{path}resourceOwnership", diagnostics);
    }

    private static void ValidateInput(
        OperationInputDefinition? input,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (input is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc101, path, "Operation input semantics are required.");
            return;
        }

        var contracts = ArchitectureValidation.OrEmpty(input.Contracts);
        if (input.AllowsNoInput && contracts.Length > 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc102,
                $"{path}/contracts",
                "An operation that allows no input cannot also declare input contracts.");
        }
        else if (!input.AllowsNoInput && contracts.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc103,
                $"{path}/contracts",
                "At least one input contract is required when input is not omitted.");
        }

        for (var index = 0; index < contracts.Length; index++)
        {
            diagnostics.Reference(contracts[index], $"{path}/contracts/{index}");
        }

        diagnostics.Required(
            input.ValidationSemantics,
            $"{path}/validationSemantics",
            "Input validation semantics");
    }

    private static void ValidateOutput(
        OperationOutputDefinition? output,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (output is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc104, path, "Operation output semantics are required.");
            return;
        }

        var contracts = ArchitectureValidation.OrEmpty(output.Contracts);
        if (output.AllowsNoOutput && contracts.Length > 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc105,
                $"{path}/contracts",
                "An operation that allows no output cannot also declare output contracts.");
        }
        else if (!output.AllowsNoOutput && contracts.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc106,
                $"{path}/contracts",
                "At least one output contract is required when output is not omitted.");
        }

        if (output.AllowsNoOutput && output.IsStreaming)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc107,
                $"{path}/isStreaming",
                "An operation without output cannot be streaming.");
        }

        for (var index = 0; index < contracts.Length; index++)
        {
            diagnostics.Reference(contracts[index], $"{path}/contracts/{index}");
        }

        diagnostics.Required(
            output.CompletionSemantics,
            $"{path}/completionSemantics",
            "Output completion semantics");
    }

    private static void ValidateSideEffects(
        OperationSideEffectDefinition? sideEffects,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (sideEffects is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc108, path, "Operation side-effect semantics are required.");
            return;
        }

        var effects = ArchitectureValidation.OrEmpty(sideEffects.Effects);
        if (sideEffects.IsSideEffectFree != (effects.Length == 0))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc109,
                path,
                "Side-effect-free must be true exactly when no effects are declared.");
        }

        for (var index = 0; index < effects.Length; index++)
        {
            var effect = effects[index];
            var itemPath = $"{path}/effects/{index}";
            diagnostics.Identifier(effect.OwnerId, $"{itemPath}/ownerId");
            diagnostics.Required(effect.Effect, $"{itemPath}/effect", "Side effect");
            diagnostics.Required(effect.CommitBoundary, $"{itemPath}/commitBoundary", "Commit boundary");
            diagnostics.Required(
                effect.CompensationPolicy,
                $"{itemPath}/compensationPolicy",
                "Compensation policy");
        }
    }

    private static void ValidateAuthority(
        OperationAuthorityDefinition? authority,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (authority is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc110, path, "Operation authority semantics are required.");
            return;
        }

        var requirements = ArchitectureValidation.OrEmpty(authority.RequirementIds);
        if (authority.IsRequired != (requirements.Length > 0))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc111,
                $"{path}/requirementIds",
                "Authority is required exactly when one or more requirements are declared.");
        }

        for (var index = 0; index < requirements.Length; index++)
        {
            diagnostics.Identifier(requirements[index], $"{path}/requirementIds/{index}");
        }

        diagnostics.Required(
            authority.EvaluationPoint,
            $"{path}/evaluationPoint",
            "Authority evaluation point");
        diagnostics.Required(
            authority.DenialSemantics,
            $"{path}/denialSemantics",
            "Authority denial semantics");
    }

    private static void ValidateFailures(
        OperationFailureSet? failures,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (failures is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc112, path, "Operation failure semantics are required.");
            return;
        }

        var declared = ArchitectureValidation.OrEmpty(failures.DeclaredFailures);
        var codes = new HashSet<string>(StringComparer.Ordinal);
        var identities = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < declared.Length; index++)
        {
            var failure = declared[index];
            var itemPath = $"{path}/declaredFailures/{index}";
            diagnostics.Identifier(failure.Identity, $"{itemPath}/identity");
            diagnostics.Required(failure.Code, $"{itemPath}/code", "Failure code");
            diagnostics.Required(failure.Meaning, $"{itemPath}/meaning", "Failure meaning");
            if (!string.IsNullOrWhiteSpace(failure.Code) && !codes.Add(failure.Code))
            {
                diagnostics.Error(ArchitectureDiagnosticIds.Pkarc113, $"{itemPath}/code", "Failure codes must be unique.");
            }

            if (!string.IsNullOrWhiteSpace(failure.Identity.Value) &&
                !identities.Add(failure.Identity.Value))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc114,
                    $"{itemPath}/identity",
                    "Failure identities must be unique.");
            }

            if (failure.DetailsContract is not null)
            {
                diagnostics.Reference(failure.DetailsContract, $"{itemPath}/detailsContract");
            }
        }

        diagnostics.Required(
            failures.UndeclaredFailurePolicy,
            $"{path}/undeclaredFailurePolicy",
            "Undeclared failure policy");
    }

    private static void ValidateCancellation(
        OperationCancellationDefinition? cancellation,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (cancellation is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc115, path, "Operation cancellation semantics are required.");
            return;
        }

        diagnostics.Required(
            cancellation.AcceptanceSemantics,
            $"{path}/acceptanceSemantics",
            "Cancellation acceptance semantics");
        diagnostics.Required(
            cancellation.PropagationSemantics,
            $"{path}/propagationSemantics",
            "Cancellation propagation semantics");
        diagnostics.Required(
            cancellation.CompletionRaceSemantics,
            $"{path}/completionRaceSemantics",
            "Cancellation completion-race semantics");
    }

    private static void ValidateIdempotency(
        OperationIdempotencyDefinition? idempotency,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (idempotency is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc116, path, "Operation idempotency semantics are required.");
            return;
        }

        if (!Enum.IsDefined(idempotency.Kind))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc124,
                $"{path}/kind",
                "The operation idempotency kind is unsupported.");
        }

        diagnostics.Required(
            idempotency.KeySemantics,
            $"{path}/keySemantics",
            "Idempotency key semantics");
        diagnostics.Required(
            idempotency.DuplicateSemantics,
            $"{path}/duplicateSemantics",
            "Duplicate request semantics");
    }

    private static void ValidateCompatibility(
        OperationCompatibilityDefinition? compatibility,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (compatibility is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc117, path, "Operation compatibility semantics are required.");
            return;
        }

        var dimensions = ArchitectureValidation.OrEmpty(compatibility.Dimensions);
        if (dimensions.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc118,
                $"{path}/dimensions",
                "At least one compatibility dimension is required.");
        }

        if (dimensions.Distinct().Count() != dimensions.Length)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc122,
                $"{path}/dimensions",
                "Compatibility dimensions must not contain duplicates.");
        }

        for (var index = 0; index < dimensions.Length; index++)
        {
            if (!Enum.IsDefined(dimensions[index]))
            {
                diagnostics.Error(
                    ArchitectureDiagnosticIds.Pkarc123,
                    $"{path}/dimensions/{index}",
                    "The compatibility dimension is unsupported.");
            }
        }

        var migrations = ArchitectureValidation.OrEmpty(compatibility.MigrationReferences);
        for (var index = 0; index < migrations.Length; index++)
        {
            diagnostics.Reference(migrations[index], $"{path}/migrationReferences/{index}");
        }

        diagnostics.Required(
            compatibility.ChangePolicy,
            $"{path}/changePolicy",
            "Compatibility change policy");
    }

    private static void ValidateObservability(
        OperationObservabilityDefinition? observability,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (observability is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc119, path, "Operation observability semantics are required.");
            return;
        }

        var signals = ArchitectureValidation.OrEmpty(observability.Signals);
        if (signals.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc120,
                $"{path}/signals",
                "At least one observability signal or an explicit 'none' signal is required.");
        }

        for (var index = 0; index < signals.Length; index++)
        {
            diagnostics.Required(signals[index], $"{path}/signals/{index}", "Observability signal");
        }

        diagnostics.Required(
            observability.CorrelationSemantics,
            $"{path}/correlationSemantics",
            "Correlation semantics");
        diagnostics.Required(
            observability.SensitiveDataPolicy,
            $"{path}/sensitiveDataPolicy",
            "Observability sensitive-data policy");
    }

    private static void ValidateResources(
        OperationResourceOwnershipDefinition? ownership,
        string path,
        ArchitectureDiagnosticBag diagnostics)
    {
        if (ownership is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc121, path, "Operation resource ownership is required.");
            return;
        }

        var resources = ArchitectureValidation.OrEmpty(ownership.Resources);
        for (var index = 0; index < resources.Length; index++)
        {
            var resource = resources[index];
            var itemPath = $"{path}/resources/{index}";
            diagnostics.Required(resource.Resource, $"{itemPath}/resource", "Resource");
            diagnostics.Identifier(resource.OwnerId, $"{itemPath}/ownerId");
            diagnostics.Required(resource.Acquisition, $"{itemPath}/acquisition", "Resource acquisition");
            diagnostics.Required(resource.Release, $"{itemPath}/release", "Resource release");
        }

        diagnostics.Required(
            ownership.DisposalSemantics,
            $"{path}/disposalSemantics",
            "Resource disposal semantics");
    }
}
