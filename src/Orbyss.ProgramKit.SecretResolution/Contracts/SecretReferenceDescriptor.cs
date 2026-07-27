namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>
/// Typed non-secret identity and exact adapter binding for protected capability resolution.
/// </summary>
public sealed record SecretReferenceDescriptor(
    [property: JsonPropertyName("identity")] ProgramKitIdentifier Identity,
    [property: JsonPropertyName("classification")] SecretReferenceClassification Classification,
    [property: JsonPropertyName("expectedResultKind")] SecretResultKind ExpectedResultKind,
    [property: JsonPropertyName("resolverCapabilityRevision")] ArtifactReference ResolverCapabilityRevision,
    [property: JsonPropertyName("locatorRevision")] ArtifactReference LocatorRevision,
    [property: JsonPropertyName("locatorClassification")] SecretReferenceClassification LocatorClassification);
