namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Metadata-only provider signal; it can never carry resolved material.</summary>
public sealed record SecretChangeSignal(
    [property: JsonPropertyName("referenceIdentity")] ProgramKitIdentifier ReferenceIdentity,
    [property: JsonPropertyName("kind")] SecretChangeKind Kind,
    [property: JsonPropertyName("previousGeneration")] long PreviousGeneration,
    [property: JsonPropertyName("lifecycle")] SecretLifecycleMetadata Lifecycle);
