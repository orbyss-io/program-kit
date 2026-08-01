using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace Orbyss.ProgramKit.Kernel.Artifacts;

public static class LogicalPaths
{
    private static readonly HashSet<string> WindowsReserved = new(StringComparer.OrdinalIgnoreCase)
    {
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    };

    public static string Normalize(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        if (Path.IsPathRooted(value) || value.Contains('\\', StringComparison.Ordinal))
        {
            throw new ArgumentException("Logical paths must be slash-separated and relative.", nameof(value));
        }

        string[] segments = value.Split('/', StringSplitOptions.RemoveEmptyEntries);
        if (segments.Length == 0 || segments.Any(static segment => segment is "." or ".."))
        {
            throw new ArgumentException("Logical path contains an empty or traversal segment.", nameof(value));
        }

        foreach (string segment in segments)
        {
            string stem = segment.Split('.')[0];
            if (WindowsReserved.Contains(stem) || segment.EndsWith(' ') || segment.EndsWith('.'))
            {
                throw new ArgumentException("Logical path contains a reserved or unstable segment.", nameof(value));
            }
        }

        return string.Join('/', segments);
    }

    public static string ResolveInside(string root, string logicalPath)
    {
        string normalized = Normalize(logicalPath);
        string resolvedRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        string candidate = Path.GetFullPath(Path.Combine(resolvedRoot, normalized.Replace('/', Path.DirectorySeparatorChar)));
        if (!candidate.StartsWith(resolvedRoot + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("Resolved path escapes the workspace.");
        }

        return candidate;
    }
}
