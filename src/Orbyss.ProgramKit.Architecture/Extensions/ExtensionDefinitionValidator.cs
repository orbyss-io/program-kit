using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Extensions;

/// <summary>Validates kind-specific extension semantics without implicit discovery.</summary>
public sealed class ExtensionDefinitionValidator :
    IProgramKitSemanticValidator<ExtensionDefinition>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ExtensionDefinition value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc200, "/", "An extension definition is required.");
            return diagnostics.ToResult();
        }

        ValidateInto(value, "/", diagnostics);
        return diagnostics.ToResult();
    }

    internal static void ValidateInto(
        ExtensionDefinition extension,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        diagnostics.Identifier(extension.Identity, $"{path}identity");
        diagnostics.Identifier(extension.OwnerId, $"{path}ownerId");
        diagnostics.Reference(extension.Contract, $"{path}contract");

        if (extension.Semantics is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc201, $"{path}semantics", "Extension semantics are required.");
            return;
        }

        var populated = 0;
        populated += extension.Semantics.Replacement is null ? 0 : 1;
        populated += extension.Semantics.AdditiveContribution is null ? 0 : 1;
        populated += extension.Semantics.EventSubscription is null ? 0 : 1;
        populated += extension.Semantics.ProviderSpecialization is null ? 0 : 1;
        populated += extension.Semantics.AdapterBridge is null ? 0 : 1;
        if (populated != 1)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc202,
                $"{path}semantics",
                "Exactly one kind-specific extension semantics object must be populated.");
        }

        switch (extension.Kind)
        {
            case ExtensionKind.Replacement:
                ValidateReplacement(extension.Semantics.Replacement, $"{path}semantics/replacement", diagnostics);
                RejectOtherKinds(extension.Semantics, ExtensionKind.Replacement, $"{path}semantics", diagnostics);
                break;
            case ExtensionKind.AdditiveContribution:
                ValidateAdditive(
                    extension.Semantics.AdditiveContribution,
                    $"{path}semantics/additiveContribution",
                    diagnostics);
                RejectOtherKinds(
                    extension.Semantics,
                    ExtensionKind.AdditiveContribution,
                    $"{path}semantics",
                    diagnostics);
                break;
            case ExtensionKind.EventSubscription:
                ValidateEvent(
                    extension.Semantics.EventSubscription,
                    $"{path}semantics/eventSubscription",
                    diagnostics);
                RejectOtherKinds(
                    extension.Semantics,
                    ExtensionKind.EventSubscription,
                    $"{path}semantics",
                    diagnostics);
                break;
            case ExtensionKind.ProviderSpecialization:
                ValidateProvider(
                    extension.Semantics.ProviderSpecialization,
                    $"{path}semantics/providerSpecialization",
                    diagnostics);
                RejectOtherKinds(
                    extension.Semantics,
                    ExtensionKind.ProviderSpecialization,
                    $"{path}semantics",
                    diagnostics);
                break;
            case ExtensionKind.AdapterBridge:
                ValidateAdapter(
                    extension.Semantics.AdapterBridge,
                    $"{path}semantics/adapterBridge",
                    diagnostics);
                RejectOtherKinds(extension.Semantics, ExtensionKind.AdapterBridge, $"{path}semantics", diagnostics);
                break;
            default:
                diagnostics.Error(ArchitectureDiagnosticIds.Pkarc203, $"{path}kind", "The extension kind is not supported.");
                break;
        }
    }

    private static void ValidateReplacement(
        ReplacementSemantics? semantics,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (semantics is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc204, path, "Replacement semantics are required.");
            return;
        }

        if (!Enum.IsDefined(semantics.Cardinality))
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc212,
                $"{path}/cardinality",
                "The replacement cardinality is unsupported.");
        }

        diagnostics.Required(semantics.SelectionRule, $"{path}/selectionRule", "Replacement selection rule");
        diagnostics.Required(
            semantics.FallbackSemantics,
            $"{path}/fallbackSemantics",
            "Replacement fallback semantics");
        diagnostics.Required(
            semantics.FailureSemantics,
            $"{path}/failureSemantics",
            "Replacement failure semantics");
    }

    private static void ValidateAdditive(
        AdditiveContributionSemantics? semantics,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (semantics is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc205, path, "Additive contribution semantics are required.");
            return;
        }

        diagnostics.Required(semantics.Cardinality, $"{path}/cardinality", "Contribution cardinality");
        diagnostics.Required(semantics.StableOrdering, $"{path}/stableOrdering", "Stable ordering");
        diagnostics.Required(
            semantics.AggregationSemantics,
            $"{path}/aggregationSemantics",
            "Aggregation semantics");
        diagnostics.Required(
            semantics.PartialOrFailFastSemantics,
            $"{path}/partialOrFailFastSemantics",
            "Partial or fail-fast behavior");
    }

    private static void ValidateEvent(
        EventSubscriptionSemantics? semantics,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (semantics is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc206, path, "Event/subscription semantics are required.");
            return;
        }

        diagnostics.Required(
            semantics.DeliveryGuarantee,
            $"{path}/deliveryGuarantee",
            "Delivery guarantee");
        diagnostics.Required(semantics.OrderingScope, $"{path}/orderingScope", "Ordering scope");
        diagnostics.Required(semantics.RetrySemantics, $"{path}/retrySemantics", "Retry semantics");
        diagnostics.Required(
            semantics.DuplicationSemantics,
            $"{path}/duplicationSemantics",
            "Duplication semantics");
        diagnostics.Required(
            semantics.HandlerFailureSemantics,
            $"{path}/handlerFailureSemantics",
            "Handler failure semantics");
    }

    private static void ValidateProvider(
        ProviderSpecializationSemantics? semantics,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (semantics is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc207, path, "Provider specialization semantics are required.");
            return;
        }

        diagnostics.Identifier(semantics.BaseProviderId, $"{path}/baseProviderId");
        var contracts = ArchitectureValidation.OrEmpty(semantics.AddedContracts);
        if (contracts.Length == 0)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc208,
                $"{path}/addedContracts",
                "A provider specialization must add at least one contract.");
        }

        for (var index = 0; index < contracts.Length; index++)
        {
            diagnostics.Reference(contracts[index], $"{path}/addedContracts/{index}");
        }

        diagnostics.Required(
            semantics.CompatibilitySemantics,
            $"{path}/compatibilitySemantics",
            "Provider compatibility semantics");
        diagnostics.Required(
            semantics.FallbackSemantics,
            $"{path}/fallbackSemantics",
            "Provider fallback semantics");
    }

    private static void ValidateAdapter(
        AdapterBridgeSemantics? semantics,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (semantics is null)
        {
            diagnostics.Error(ArchitectureDiagnosticIds.Pkarc209, path, "Adapter/bridge semantics are required.");
            return;
        }

        diagnostics.Identifier(semantics.FirstSideOwnerId, $"{path}/firstSideOwnerId");
        diagnostics.Identifier(semantics.SecondSideOwnerId, $"{path}/secondSideOwnerId");
        if (semantics.FirstSideOwnerId == semantics.SecondSideOwnerId)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc210,
                path,
                "An adapter/bridge must name two different owned sides.");
        }

        diagnostics.Required(
            semantics.TranslationSemantics,
            $"{path}/translationSemantics",
            "Translation semantics");
        diagnostics.Required(semantics.LossPolicy, $"{path}/lossPolicy", "Translation loss policy");
        diagnostics.Required(
            semantics.AuthoritySemantics,
            $"{path}/authoritySemantics",
            "Adapter authority semantics");
        diagnostics.Required(
            semantics.FailureSemantics,
            $"{path}/failureSemantics",
            "Adapter failure semantics");
        diagnostics.Required(
            semantics.ObservabilitySemantics,
            $"{path}/observabilitySemantics",
            "Adapter observability semantics");
    }

    private static void RejectOtherKinds(
        ExtensionSemantics semantics,
        ExtensionKind expected,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var mismatch =
            (expected != ExtensionKind.Replacement && semantics.Replacement is not null) ||
            (expected != ExtensionKind.AdditiveContribution && semantics.AdditiveContribution is not null) ||
            (expected != ExtensionKind.EventSubscription && semantics.EventSubscription is not null) ||
            (expected != ExtensionKind.ProviderSpecialization && semantics.ProviderSpecialization is not null) ||
            (expected != ExtensionKind.AdapterBridge && semantics.AdapterBridge is not null);
        if (mismatch)
        {
            diagnostics.Error(
                ArchitectureDiagnosticIds.Pkarc211,
                path,
                "Populated extension semantics must match the selected extension kind.");
        }
    }
}
