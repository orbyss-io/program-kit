namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Minimum and maximum values accepted by one console element.</summary>
public sealed record ConsoleValueArity(
    [property: JsonPropertyName("minimum")] int Minimum,
    [property: JsonPropertyName("maximum")] int Maximum);
