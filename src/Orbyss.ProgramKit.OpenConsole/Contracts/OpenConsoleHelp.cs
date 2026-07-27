namespace Orbyss.ProgramKit.OpenConsole.Contracts;

/// <summary>Generated help option and output behavior.</summary>
public sealed record OpenConsoleHelp(
    [property: JsonPropertyName("longOption")] string LongOption,
    [property: JsonPropertyName("shortOption")] string ShortOption,
    [property: JsonPropertyName("exitCode")] int ExitCode);
