namespace Orbyss.ProgramKit.DotNet.Documentation.Console;

/// <summary>Minimum and maximum occurrences accepted in one invocation.</summary>
public sealed record ConsoleOccurrence(
    [property: JsonPropertyName("minimum")] int Minimum,
    [property: JsonPropertyName("maximum")] int Maximum);
