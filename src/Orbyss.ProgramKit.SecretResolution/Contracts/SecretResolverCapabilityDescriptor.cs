namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Exact provider-neutral mechanical capabilities of one selected resolver adapter.</summary>
public sealed record SecretResolverCapabilityDescriptor(
    [property: JsonPropertyName("capabilityRevision")] ArtifactReference CapabilityRevision,
    [property: JsonPropertyName("supportedResultKinds")] ImmutableArray<SecretResultKind> SupportedResultKinds,
    [property: JsonPropertyName("supportedLifetimes")] ImmutableArray<SecretResultLifetime> SupportedLifetimes,
    [property: JsonPropertyName("supportedReferenceClassifications")] ImmutableArray<SecretReferenceClassification> SupportedReferenceClassifications,
    [property: JsonPropertyName("supportedLocatorClassifications")] ImmutableArray<SecretReferenceClassification> SupportedLocatorClassifications,
    [property: JsonPropertyName("rotationCapability")] SecretRotationCapability RotationCapability);
