using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Orbyss.ProgramKit.SpecKitAdapter.Publication;

public static class LogicalPathPolicy
{
    public static string Resolve(string workspaceRoot, string logicalPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(workspaceRoot);
        ArgumentException.ThrowIfNullOrWhiteSpace(logicalPath);
        if (Path.IsPathRooted(logicalPath) || logicalPath.Contains('\\'))
        {
            throw new InvalidDataException("A logical path must be relative and use forward slashes.");
        }

        string[] segments = logicalPath.Split('/', StringSplitOptions.None);
        if (segments.Any(static segment => segment.Length == 0 || segment is "." or ".."))
        {
            throw new InvalidDataException("A logical path cannot contain empty, current, or parent segments.");
        }

        string root = Path.GetFullPath(workspaceRoot);
        string candidate = Path.GetFullPath(Path.Combine(root, Path.Combine(segments)));
        StringComparison comparison = OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
        if (!candidate.StartsWith(root + Path.DirectorySeparatorChar, comparison))
        {
            throw new InvalidDataException("The logical path escapes the workspace.");
        }

        RejectReparseChain(root, segments);
        return candidate;
    }

    public static void ValidateDistinct(IEnumerable<string> logicalPaths)
    {
        string[] paths = logicalPaths.ToArray();
        if (paths.Any(static path => string.IsNullOrWhiteSpace(path)) ||
            paths.Distinct(StringComparer.Ordinal).Count() != paths.Length ||
            paths.Distinct(StringComparer.OrdinalIgnoreCase).Count() != paths.Length)
        {
            throw new InvalidDataException("Logical paths contain a duplicate or case collision.");
        }
    }

    private static void RejectReparseChain(string root, IReadOnlyList<string> segments)
    {
        string current = root;
        foreach (string segment in segments)
        {
            current = Path.Combine(current, segment);
            FileSystemInfo? info = Directory.Exists(current)
                ? new DirectoryInfo(current)
                : File.Exists(current) ? new FileInfo(current) : null;
            if (info is not null && (info.Attributes & FileAttributes.ReparsePoint) != 0)
            {
                throw new InvalidDataException("Logical paths cannot traverse a reparse point.");
            }
        }
    }
}
