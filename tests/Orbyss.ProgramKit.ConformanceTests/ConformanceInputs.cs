using System.Collections.Immutable;

namespace Orbyss.ProgramKit.ConformanceTests;

internal static class ConformanceInputs
{
    private static readonly string Root =
        Path.Combine(AppContext.BaseDirectory, "ConformanceInputs");

    public static string Read(string relativePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relativePath);
        return File.ReadAllText(Path.Combine(Root, relativePath));
    }

    public static ImmutableArray<string> Files(string relativeDirectory, string pattern)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relativeDirectory);
        ArgumentException.ThrowIfNullOrWhiteSpace(pattern);

        var directory = Path.Combine(Root, relativeDirectory);
        return Directory
            .EnumerateFiles(directory, pattern, SearchOption.AllDirectories)
            .Order(StringComparer.Ordinal)
            .ToImmutableArray();
    }
}
