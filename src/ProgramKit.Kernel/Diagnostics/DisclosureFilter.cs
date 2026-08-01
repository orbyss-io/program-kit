using System;
using System.IO;

namespace Orbyss.ProgramKit.Kernel.Diagnostics;

public static class DisclosureFilter
{
    public static string SafeLogicalValue(string value)
    {
        if (IsAbsolutePath(value) || value.Contains("..", StringComparison.Ordinal))
        {
            return "withheld";
        }

        return SafeText(value);
    }

    public static string SafeText(string value)
    {
        string singleLine = value.Replace("\r", " ", StringComparison.Ordinal).Replace("\n", " ", StringComparison.Ordinal);

        string[] sensitiveMarkers = { "password", "secret", "token=", "apikey", "authorization:", "bearer ", "stack trace", "conversation id", "raw tool output" };
        foreach (string marker in sensitiveMarkers)
        {
            if (singleLine.Contains(marker, StringComparison.OrdinalIgnoreCase))
            {
                return "withheld";
            }
        }
        char[] sanitized = singleLine.ToCharArray();
        for (int index = 0; index < sanitized.Length; index++)
        {
            if (char.IsControl(sanitized[index])) sanitized[index] = ' ';
        }

        const string suffix = "[truncated]";
        string safe = new(sanitized);
        return safe.Length <= 500 ? safe : safe[..(500 - suffix.Length)] + suffix;


    }

    public static string SafeToolOutput(string value) => "withheld";

    private static bool IsAbsolutePath(string value) =>
        Path.IsPathRooted(value) ||
        value.StartsWith("\\\\", StringComparison.Ordinal) ||
        (value.Length >= 3 &&
         char.IsAsciiLetter(value[0]) &&
         value[1] == ':' &&
         (value[2] == '\\' || value[2] == '/'));
}
