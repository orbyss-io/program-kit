namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Cross-platform path rules for generated payloads and sibling artifacts.</summary>
public static class GeneratedOutputPathPolicy
{
    private static readonly HashSet<string> WindowsDeviceNames =
        new(
            [
                "CON", "PRN", "AUX", "NUL",
                "COM1", "COM2", "COM3", "COM4", "COM5",
                "COM6", "COM7", "COM8", "COM9",
                "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
                "LPT6", "LPT7", "LPT8", "LPT9",
            ],
            StringComparer.OrdinalIgnoreCase);

    /// <summary>Validates and returns one already-normalized portable relative path.</summary>
    public static string RequireNormalizedRelativePath(string path)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            Path.IsPathRooted(path) ||
            path.Contains('\\') ||
            path.Contains('\0'))
        {
            throw new InvalidDataException(
                "A generated-output path must be a normalized relative path.");
        }

        var segments = path.Split('/');
        if (segments.Any(static segment =>
                segment.Length == 0 ||
                segment is "." or ".." ||
                segment.EndsWith(' ') ||
                segment.EndsWith('.') ||
                segment.Any(static character =>
                    character < ' ' ||
                    character is '"' or '<' or '>' or '|' or ':' or '*' or '?') ||
                IsWindowsDeviceName(segment)))
        {
            throw new InvalidDataException(
                "A generated-output path contains an unsafe segment.");
        }

        if (string.Equals(
                path,
                GeneratedOutputIntegrityConstants.ManifestRelativePath,
                StringComparison.Ordinal))
        {
            throw new InvalidDataException(
                "The generated-output manifest path is reserved.");
        }

        return path;
    }

    /// <summary>Returns the deterministic external-anchor path for a generated root.</summary>
    public static string AnchorPath(string rootPath) =>
        string.Concat(
            RequireAbsoluteRoot(rootPath),
            GeneratedOutputIntegrityConstants.AnchorSuffix);

    /// <summary>Returns the deterministic recoverable transaction path for a generated root.</summary>
    public static string TransactionPath(string rootPath) =>
        string.Concat(
            RequireAbsoluteRoot(rootPath),
            GeneratedOutputIntegrityConstants.TransactionSuffix);

    /// <summary>Resolves a normalized payload path and proves it remains under the root.</summary>
    public static string ResolveUnderRoot(
        string rootPath,
        string relativePath,
        bool allowManifest = false)
    {
        var root = RequireAbsoluteRoot(rootPath);
        if (allowManifest &&
            string.Equals(
                relativePath,
                GeneratedOutputIntegrityConstants.ManifestRelativePath,
                StringComparison.Ordinal))
        {
            // The manifest is the only caller-approved reserved path.
        }
        else
        {
            RequireNormalizedRelativePath(relativePath);
        }

        var resolved = Path.GetFullPath(
            Path.Combine(
                [root, .. relativePath.Split('/')]));
        var prefix = string.Concat(
            root.TrimEnd(Path.DirectorySeparatorChar),
            Path.DirectorySeparatorChar);
        if (!resolved.StartsWith(prefix, PathComparison))
        {
            throw new InvalidDataException(
                "A generated-output path escapes its declared root.");
        }

        return resolved;
    }

    /// <summary>Returns a normalized absolute root without a trailing separator.</summary>
    public static string RequireAbsoluteRoot(string rootPath)
    {
        if (string.IsNullOrWhiteSpace(rootPath))
        {
            throw new InvalidDataException(
                "A generated-output root is required.");
        }

        var fullPath = Path.GetFullPath(rootPath);
        var fileSystemRoot = Path.GetPathRoot(fullPath);
        if (string.Equals(
                fullPath,
                fileSystemRoot,
                PathComparison))
        {
            throw new InvalidDataException(
                "A filesystem root cannot be a generated-output root.");
        }

        return fullPath.TrimEnd(Path.DirectorySeparatorChar);
    }

    internal static StringComparison PathComparison =>
        OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    private static bool IsWindowsDeviceName(string segment)
    {
        var stem = segment.Split('.')[0];
        return WindowsDeviceNames.Contains(stem);
    }
}
