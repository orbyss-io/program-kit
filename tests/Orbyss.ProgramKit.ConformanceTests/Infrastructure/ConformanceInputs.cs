using System.Collections.Immutable;

namespace Orbyss.ProgramKit.ConformanceTests.Infrastructure;

internal static class ConformanceInputs
{
    private static readonly string Root =
        Path.Combine(AppContext.BaseDirectory, "ConformanceInputs");
    private static readonly string Repository = FindRepositoryRoot();

    public static string RepositoryRoot => Repository;

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

    private static string FindRepositoryRoot()
    {
        DirectoryInfo? candidate = new(AppContext.BaseDirectory);
        while (candidate is not null)
        {
            if (File.Exists(Path.Combine(candidate.FullName, "global.json")) &&
                Directory.Exists(Path.Combine(candidate.FullName, "program-kit")))
            {
                return candidate.FullName;
            }

            candidate = candidate.Parent;
        }

        throw new DirectoryNotFoundException(
            "Could not locate the repository root from the test output directory.");
    }
}
