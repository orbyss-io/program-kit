namespace Orbyss.ProgramKit.DotNet.Documentation.Console;

/// <summary>Generated completion query behavior.</summary>
public sealed record OpenConsoleCompletion(
    [property: JsonPropertyName("longOption")] string LongOption,
    [property: JsonPropertyName("includesAliases")] bool IncludesAliases,
    [property: JsonPropertyName("includesValueHints")] bool IncludesValueHints);
