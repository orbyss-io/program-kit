namespace Orbyss.ProgramKit.Operations.Contracts;

/// <summary>An immutable, explicitly composed finite operation catalog.</summary>
public sealed record OperationContractCatalog(
    [property: JsonPropertyName("operations")]
    ImmutableArray<OperationContractDescriptor> Operations);
