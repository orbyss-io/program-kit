namespace Orbyss.ProgramKit.SecretResolution.Contracts;

/// <summary>Complete provider-neutral contract for one typed secret consumption boundary.</summary>
public sealed record SecretResolutionContract(
    [property: JsonPropertyName("reference")] SecretReferenceDescriptor Reference,
    [property: JsonPropertyName("resolver")] SecretResolverCapabilityDescriptor Resolver,
    [property: JsonPropertyName("consumption")] SecretConsumptionBinding Consumption);
