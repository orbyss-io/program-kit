using System;
using System.IO;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static class DisclosureFilter
{
    public static string SafeLogicalValue(string value)
    {
        if (Path.IsPathRooted(value) || value.Contains("..", StringComparison.Ordinal))
        {
            return "withheld";
        }

        return SafeText(value);
    }

    public static string SafeText(string value)
    {
        string singleLine = value.Replace("\r", " ", StringComparison.Ordinal).Replace("\n", " ", StringComparison.Ordinal);
        if (singleLine.Length > 500)
        {
            singleLine = singleLine[..500];
        }

        string[] sensitiveMarkers = { "password", "secret", "token=", "apikey", "stack trace" };
        foreach (string marker in sensitiveMarkers)
        {
            if (singleLine.Contains(marker, StringComparison.OrdinalIgnoreCase))
            {
                return "withheld";
            }
        }

        return singleLine;
    }
}
