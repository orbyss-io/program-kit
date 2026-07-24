namespace Orbyss.ProgramKit.DotNet.Documentation.Console;

/// <summary>Token-array example and its stable explanation.</summary>
public sealed record OpenConsoleExample(
    [property: JsonPropertyName("tokens")] ImmutableArray<string> Tokens,
    [property: JsonPropertyName("summary")] string Summary);
