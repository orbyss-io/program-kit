using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Orbyss.ProgramKit.Cli.Parsing;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Operations;

namespace Orbyss.ProgramKit.Cli.Rendering;

public static class ResultRenderer
{
    public static void Write(OperationResult result, OutputFormat format, Stream stdout)
    {
        byte[] bytes = format == OutputFormat.Json
            ? OperationResultProjector.ToCanonicalBytes(result)
            : Encoding.UTF8.GetBytes(Text(result));
        stdout.Write(bytes);
        if (format == OutputFormat.Text)
        {
            stdout.WriteByte((byte)'\n');
        }
    }

    private static string Text(OperationResult result)
    {
        StringBuilder builder = new();
        builder.AppendLine(CultureInfo.InvariantCulture, $"command: {Kebab(result.Command)}");
        builder.AppendLine(CultureInfo.InvariantCulture, $"outcome: {Kebab(result.Outcome)}");
        builder.AppendLine(CultureInfo.InvariantCulture, $"furthest phase: {Kebab(result.FurthestPhase)}");
        builder.AppendLine(CultureInfo.InvariantCulture, $"effect state: {Kebab(result.EffectState)}");
        builder.AppendLine(CultureInfo.InvariantCulture, $"primary disposition: {Kebab(result.PrimaryDisposition)}");
        if (result.ConstructionIdentity is not null)
        {
            builder.AppendLine(CultureInfo.InvariantCulture, $"construction identity: {result.ConstructionIdentity}");
        }

        foreach (Orbyss.ProgramKit.Contracts.Diagnostics.Diagnostic diagnostic in result.Diagnostics.Items)
        {
            builder.AppendLine(CultureInfo.InvariantCulture, $"{diagnostic.Id}: {diagnostic.MessageKey} ({diagnostic.Cause})");
        }

        if (result.Explanation is not null)
        {
            builder.AppendLine("integration resolution explanation: available inline");
        }

        if (result.Utility is not null)
        {
            foreach ((string key, System.Text.Json.Nodes.JsonNode? value) in result.Utility.OrderBy(static item => item.Key, StringComparer.Ordinal))
            {
                builder.AppendLine(CultureInfo.InvariantCulture, $"{key}: {value?.ToJsonString()}");
            }
        }

        return builder.ToString().TrimEnd();
    }

    private static string Kebab<T>(T value)
        where T : struct, Enum
    {
        string text = value.ToString();
        StringBuilder builder = new();
        for (int index = 0; index < text.Length; index++)
        {
            if (index > 0 && char.IsUpper(text[index]))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(text[index]));
        }

        return builder.ToString();
    }
}
