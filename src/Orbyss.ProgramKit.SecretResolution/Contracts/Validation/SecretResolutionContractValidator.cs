using Orbyss.ProgramKit.SecretResolution.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.SecretResolution.Contracts.Validation;

/// <summary>Validates provider, result, lifetime, rotation, and reaction compatibility.</summary>
public sealed class SecretResolutionContractValidator :
    IProgramKitSemanticValidator<SecretResolutionContract>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(SecretResolutionContract value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        Validate(value, "$", diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    internal static void Validate(
        SecretResolutionContract value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value.Reference is null)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.MissingRequiredValue,
                "A typed secret reference is required.",
                string.Concat(path, ".reference")));
            return;
        }

        if (value.Resolver is null)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.MissingRequiredValue,
                "An exact resolver capability is required.",
                string.Concat(path, ".resolver")));
            return;
        }

        if (value.Consumption is null)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.MissingRequiredValue,
                "An explicit consumer binding is required.",
                string.Concat(path, ".consumption")));
            return;
        }

        ValidateReference(value.Reference, string.Concat(path, ".reference"), diagnostics);
        ValidateResolver(value.Resolver, string.Concat(path, ".resolver"), diagnostics);
        ValidateConsumption(value.Consumption, string.Concat(path, ".consumption"), diagnostics);
        ValidateCompatibility(value, path, diagnostics);
    }

    private static void ValidateReference(
        SecretReferenceDescriptor value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        SecretResolutionValidation.RequireIdentifier(
            value.Identity,
            string.Concat(path, ".identity"),
            diagnostics);
        SecretResolutionValidation.ValidateClassification(
            value.Classification,
            string.Concat(path, ".classification"),
            diagnostics);
        SecretResolutionValidation.ValidateEnum(
            value.ExpectedResultKind,
            string.Concat(path, ".expectedResultKind"),
            diagnostics);
        if (value.ExpectedResultKind == SecretResultKind.Unspecified)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.UnsupportedResultKind,
                "An expected result capability must be selected.",
                string.Concat(path, ".expectedResultKind")));
        }

        SecretResolutionValidation.ValidateReference(
            value.ResolverCapabilityRevision,
            "capability",
            string.Concat(path, ".resolverCapabilityRevision"),
            diagnostics);
        SecretResolutionValidation.ValidateReference(
            value.LocatorRevision,
            "locator",
            string.Concat(path, ".locatorRevision"),
            diagnostics);
        SecretResolutionValidation.ValidateClassification(
            value.LocatorClassification,
            string.Concat(path, ".locatorClassification"),
            diagnostics);
    }

    private static void ValidateResolver(
        SecretResolverCapabilityDescriptor value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        SecretResolutionValidation.ValidateReference(
            value.CapabilityRevision,
            "capability",
            string.Concat(path, ".capabilityRevision"),
            diagnostics);
        SecretResolutionValidation.ValidateFiniteSet(
            value.SupportedResultKinds,
            string.Concat(path, ".supportedResultKinds"),
            diagnostics,
            SecretResultKind.Unspecified);
        SecretResolutionValidation.ValidateFiniteSet(
            value.SupportedLifetimes,
            string.Concat(path, ".supportedLifetimes"),
            diagnostics,
            SecretResultLifetime.Unspecified);
        SecretResolutionValidation.ValidateFiniteSet(
            value.SupportedReferenceClassifications,
            string.Concat(path, ".supportedReferenceClassifications"),
            diagnostics,
            SecretReferenceClassification.Unspecified);
        SecretResolutionValidation.ValidateFiniteSet(
            value.SupportedLocatorClassifications,
            string.Concat(path, ".supportedLocatorClassifications"),
            diagnostics,
            SecretReferenceClassification.Unspecified);
        SecretResolutionValidation.ValidateEnum(
            value.RotationCapability,
            string.Concat(path, ".rotationCapability"),
            diagnostics);
    }

    private static void ValidateConsumption(
        SecretConsumptionBinding value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        SecretResolutionValidation.ValidateEnum(
            value.RequestedLifetime,
            string.Concat(path, ".requestedLifetime"),
            diagnostics);
        if (value.RequestedLifetime == SecretResultLifetime.Unspecified)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.UnsupportedLifetime,
                "A result lifetime must be selected.",
                string.Concat(path, ".requestedLifetime")));
        }

        SecretResolutionValidation.ValidateEnum(
            value.ConsumptionShape,
            string.Concat(path, ".consumptionShape"),
            diagnostics);
        if (value.ConsumptionShape == SecretConsumptionShape.Unspecified)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidConfigurationProjection,
                "A native or configuration consumption shape must be selected.",
                string.Concat(path, ".consumptionShape")));
        }

        SecretResolutionValidation.ValidateEnum(
            value.Reaction,
            string.Concat(path, ".reaction"),
            diagnostics);
    }

    private static void ValidateCompatibility(
        SecretResolutionContract value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var reference = value.Reference;
        var resolver = value.Resolver;
        var consumption = value.Consumption;
        if (reference.ResolverCapabilityRevision is not null &&
            resolver.CapabilityRevision is not null &&
            !string.Equals(
                SecretResolutionValidation.ExactKey(reference.ResolverCapabilityRevision),
                SecretResolutionValidation.ExactKey(resolver.CapabilityRevision),
                StringComparison.Ordinal))
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidReference,
                "The reference must select this exact resolver capability revision.",
                string.Concat(path, ".reference.resolverCapabilityRevision")));
        }

        if (!resolver.SupportedResultKinds.IsDefault &&
            !resolver.SupportedResultKinds.Contains(reference.ExpectedResultKind))
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.UnsupportedResultKind,
                "The selected resolver does not support the expected result capability.",
                string.Concat(path, ".reference.expectedResultKind")));
        }

        if (!resolver.SupportedLifetimes.IsDefault &&
            !resolver.SupportedLifetimes.Contains(consumption.RequestedLifetime))
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.UnsupportedLifetime,
                "The selected resolver does not support the requested result lifetime.",
                string.Concat(path, ".consumption.requestedLifetime")));
        }

        if ((!resolver.SupportedReferenceClassifications.IsDefault &&
             !resolver.SupportedReferenceClassifications.Contains(reference.Classification)) ||
            (!resolver.SupportedLocatorClassifications.IsDefault &&
             !resolver.SupportedLocatorClassifications.Contains(reference.LocatorClassification)))
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.UnclassifiedReference,
                "The resolver does not support the selected reference and locator classifications.",
                string.Concat(path, ".reference")));
        }

        if (consumption.ConsumptionShape == SecretConsumptionShape.Configuration &&
            reference.ExpectedResultKind is not SecretResultKind.ConfigurationText and
                not SecretResultKind.ConfigurationBytes)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.InvalidConfigurationProjection,
                "Only configuration text or bytes may enter configuration mechanics.",
                string.Concat(path, ".consumption.consumptionShape")));
        }

        if (consumption.RotationRequired &&
            resolver.RotationCapability == SecretRotationCapability.Unsupported)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.IncompatibleReaction,
                "Required rotation needs an expiry or metadata-only change capability.",
                string.Concat(path, ".resolver.rotationCapability")));
        }

        if (consumption.RotationRequired &&
            consumption.Reaction == SecretConsumerReaction.Unsupported)
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.IncompatibleReaction,
                "A consumer requiring rotation must select a supported reaction or manual handling.",
                string.Concat(path, ".consumption.reaction")));
        }

        if (!IsReactionCompatible(reference.ExpectedResultKind, consumption.Reaction))
        {
            diagnostics.Add(SecretResolutionValidation.Error(
                SecretResolutionDiagnosticIds.IncompatibleReaction,
                "The selected result capability and consumer reaction are not compatible.",
                string.Concat(path, ".consumption.reaction")));
        }
    }

    private static bool IsReactionCompatible(
        SecretResultKind resultKind,
        SecretConsumerReaction reaction)
    {
        if (reaction is SecretConsumerReaction.HostRestartRequest or
            SecretConsumerReaction.Manual or
            SecretConsumerReaction.Unsupported)
        {
            return true;
        }

        return resultKind switch
        {
            SecretResultKind.ConfigurationText or
            SecretResultKind.ConfigurationBytes =>
                reaction == SecretConsumerReaction.HotReplacement,
            SecretResultKind.Certificate =>
                reaction is SecretConsumerReaction.HotReplacement or
                    SecretConsumerReaction.ClientRecreation or
                    SecretConsumerReaction.Reconnect,
            SecretResultKind.MountedFileHandle =>
                reaction is SecretConsumerReaction.Reconnect or
                    SecretConsumerReaction.ResourceRecycle,
            SecretResultKind.CredentialHandle or
            SecretResultKind.WorkloadIdentityCapability =>
                reaction is SecretConsumerReaction.ClientRecreation or
                    SecretConsumerReaction.Reconnect or
                    SecretConsumerReaction.ResourceRecycle,
            SecretResultKind.AssertionService =>
                reaction is SecretConsumerReaction.HotReplacement or
                    SecretConsumerReaction.ClientRecreation or
                    SecretConsumerReaction.Reconnect,
            _ => false,
        };
    }
}
