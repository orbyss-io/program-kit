namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Validated prior ownership used only by explicit initialization.</summary>
internal sealed record PreviousState(
    string[] ProviderNames,
    IReadOnlyDictionary<string, string> OutputDigests,
    string[] LegacyOutputPaths)
{
    /// <summary>Gets an empty prior state.</summary>
    internal static PreviousState Empty { get; } =
        new(
            [],
            new Dictionary<string, string>(StringComparer.Ordinal),
            []);
}
