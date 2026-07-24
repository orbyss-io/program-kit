namespace Orbyss.ProgramKit.CommandLine.Operations.Local;

/// <summary>Fixed path validation and normalization for explicit local operations.</summary>
internal static class LocalOperationPaths
{
    internal static string ResolveSourceRoot(
        string manifestPath,
        string sourceRoot)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(manifestPath);
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceRoot);
        var manifestDirectory = Path.GetDirectoryName(
            Path.GetFullPath(manifestPath)) ??
            throw new InvalidDataException(
                "The explicit manifest path has no parent directory.");
        return Path.GetFullPath(sourceRoot, manifestDirectory);
    }

    internal static string ResolveBelow(
        string root,
        string relativePath,
        string description)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(root);
        RequireNormalizedRelativePath(relativePath, description);
        var fullRoot = Path.GetFullPath(root);
        var resolved = Path.GetFullPath(
            relativePath.Replace('/', Path.DirectorySeparatorChar),
            fullRoot);
        EnsureBelow(fullRoot, resolved, description);
        return resolved;
    }

    internal static string RelativeTo(string root, string path)
    {
        var fullRoot = Path.GetFullPath(root);
        var fullPath = Path.GetFullPath(path);
        EnsureBelow(fullRoot, fullPath, "The reported path");
        return Path.GetRelativePath(fullRoot, fullPath)
            .Replace(Path.DirectorySeparatorChar, '/');
    }

    internal static string HostSegment(string identity) =>
        Uri.EscapeDataString(identity);

    internal static void EnsureOutputAbsent(string outputPath)
    {
        var fullPath = Path.GetFullPath(outputPath);
        if (Path.GetPathRoot(fullPath) == fullPath)
        {
            throw new InvalidDataException(
                "An operation output cannot be a filesystem root.");
        }

        if (File.Exists(fullPath) || Directory.Exists(fullPath))
        {
            throw new IOException(
                string.Concat(
                    "The explicit output already exists: ",
                    fullPath));
        }
    }

    internal static void EnsureSafeRoot(string rootPath)
    {
        var fullPath = Path.GetFullPath(rootPath);
        if (Path.GetPathRoot(fullPath) == fullPath || File.Exists(fullPath))
        {
            throw new InvalidDataException(
                "An operation root must be a non-root directory path.");
        }
    }

    internal static void RequireNormalizedRelativePath(
        string relativePath,
        string description)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(relativePath);
        if (Path.IsPathRooted(relativePath) ||
            relativePath.Contains('\\', StringComparison.Ordinal) ||
            relativePath.Split('/').Any(static part =>
                part.Length == 0 ||
                string.Equals(part, ".", StringComparison.Ordinal) ||
                string.Equals(part, "..", StringComparison.Ordinal)))
        {
            throw new InvalidDataException(
                string.Concat(
                    description,
                    " must be a normalized forward-slash relative path."));
        }
    }

    private static void EnsureBelow(
        string root,
        string candidate,
        string description)
    {
        var comparison = OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;
        var rootPrefix = string.Concat(
            root.TrimEnd(
                Path.DirectorySeparatorChar,
                Path.AltDirectorySeparatorChar),
            Path.DirectorySeparatorChar);
        if (!candidate.StartsWith(rootPrefix, comparison))
        {
            throw new InvalidDataException(
                string.Concat(description, " must remain below its declared root."));
        }
    }
}
