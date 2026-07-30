namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>Versioned product-owned Open Console authoring style.</summary>
public sealed record DotNetConsoleContractStyleCatalog(
    [property: JsonPropertyName("identity")] string Identity,
    [property: JsonPropertyName("version")] string Version,
    [property: JsonPropertyName("openConsoleVersion")]
    string OpenConsoleVersion,
    [property: JsonPropertyName("materializationRequestVersion")]
    string MaterializationRequestVersion,
    [property: JsonPropertyName("commandSketchVersion")]
    string CommandSketchVersion,
    [property: JsonPropertyName("rules")]
    ImmutableArray<DotNetConsoleContractStyleRule> Rules,
    [property: JsonPropertyName("logicalClrTypes")]
    ImmutableArray<DotNetConsoleLogicalClrType> LogicalClrTypes,
    [property: JsonPropertyName("commands")]
    DotNetConsoleContractStyleCommands Commands);
