namespace Orbyss.ProgramKit.DotNet.Documentation.Console;

/// <summary>Frozen operating-system-token parsing conventions.</summary>
public sealed record OpenConsoleParsing(
    [property: JsonPropertyName("consumesOperatingSystemTokenArray")] bool ConsumesOperatingSystemTokenArray,
    [property: JsonPropertyName("optionTerminator")] string OptionTerminator,
    [property: JsonPropertyName("supportsLongEqualsSyntax")] bool SupportsLongEqualsSyntax,
    [property: JsonPropertyName("caseSensitive")] bool CaseSensitive,
    [property: JsonPropertyName("conversionCulture")] string ConversionCulture,
    [property: JsonPropertyName("duplicateOptionPolicy")] string DuplicateOptionPolicy);
