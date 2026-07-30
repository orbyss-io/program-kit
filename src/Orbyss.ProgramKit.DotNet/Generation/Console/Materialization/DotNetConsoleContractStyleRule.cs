namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>One stable Console contract-style rule.</summary>
public sealed record DotNetConsoleContractStyleRule(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("summary")] string Summary);
