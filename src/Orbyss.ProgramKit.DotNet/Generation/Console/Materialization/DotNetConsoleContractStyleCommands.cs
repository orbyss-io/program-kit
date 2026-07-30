namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>Finite backed commands associated with the Console contract style.</summary>
public sealed record DotNetConsoleContractStyleCommands(
    [property: JsonPropertyName("describe")] string Describe,
    [property: JsonPropertyName("scaffold")] string Scaffold,
    [property: JsonPropertyName("materialize")] string Materialize);
