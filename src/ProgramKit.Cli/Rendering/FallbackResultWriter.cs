using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Cli.Rendering;

internal static class FallbackResultWriter
{
    public static void Write(PublicCommand command, OperationPhase phase, EffectState effect, Stream output)
    {
        string occurrence = Digest($"program-kit.kernel/PKINT0001\n{command}\n{phase}\n{effect}");
        using Utf8JsonWriter writer = new(output, new JsonWriterOptions { Indented = false });
        writer.WriteStartObject();
        writer.WriteStartArray("artifacts"); writer.WriteEndArray();
        writer.WriteString("canonicalProfile", "program-kit.canonical-json/v1");
        writer.WriteStartArray("changes"); writer.WriteEndArray();
        writer.WriteString("command", Kebab(command));
        writer.WriteStartObject("diagnostics");
        writer.WriteString("fullCollectionDigest", Digest(occurrence));
        writer.WriteString("grouping", "program-kit.diagnostic-grouping/v1");
        writer.WriteStartArray("items");
        writer.WriteStartObject();
        writer.WriteStartObject("catalog"); Identity(writer, "orbyss.program-kit", "diagnostic-catalog", "kernel", "1.0.0"); writer.WriteEndObject();
        writer.WriteString("category", "internal");
        writer.WriteStartObject("cause");
        writer.WriteStartArray("details"); SafeValue(writer, "The normal result pipeline could not complete."); writer.WriteEndArray();
        writer.WriteString("kind", "bounded"); writer.WriteEndObject();
        writer.WriteStartObject("consequence"); writer.WriteStartArray("affectedClaims"); writer.WriteStringValue("operation-trust"); writer.WriteEndArray(); writer.WriteString("kind", "bounded"); writer.WriteEndObject();
        writer.WriteStartArray("documentation"); writer.WriteEndArray();
        writer.WriteStartArray("evidence"); writer.WriteEndArray();
        writer.WriteString("id", "program-kit.kernel/PKINT0001");
        writer.WriteString("messageKey", "internal.pipeline-failure");
        writer.WriteNumber("occurrenceCount", 1);
        writer.WriteString("occurrenceKey", occurrence);
        writer.WriteStartObject("parameters"); writer.WriteEndObject();
        writer.WriteString("phase", Kebab(phase));
        writer.WriteStartArray("remediations"); writer.WriteEndArray();
        writer.WriteStartObject("rule"); Identity(writer, "orbyss.program-kit", "rule", "internal.pipeline-failure", "1.0.0"); writer.WriteEndObject();
        writer.WriteString("severity", "fatal");
        writer.WriteStartArray("subjects");
        writer.WriteStartObject();
        writer.WriteStartObject("identity"); Identity(writer, "orbyss.program-kit", "operation-contract", Kebab(command), "1.0.0"); writer.WriteEndObject();
        writer.WriteString("kind", "public-command");
        writer.WriteEndObject();
        writer.WriteEndArray();
        writer.WriteEndObject();
        writer.WriteEndArray();
        writer.WriteNumber("omitted", 0);
        writer.WriteNumber("returned", 1);
        writer.WriteNumber("total", 1);
        writer.WriteEndObject();
        writer.WriteString("effectState", Kebab(effect));
        writer.WriteStartArray("evidence"); writer.WriteEndArray();
        writer.WriteString("furthestPhase", Kebab(phase));
        writer.WriteStartObject("operationContract"); Identity(writer, "orbyss.program-kit", "operation-contract", Kebab(command), "1.0.0"); writer.WriteEndObject();
        writer.WriteString("outcome", "faulted");
        writer.WriteString("primaryDisposition", "stop");
        writer.WriteStartArray("receipts"); writer.WriteEndArray();
        writer.WriteString("schema", "program-kit.operation-result/v1");
        writer.WriteEndObject();
        writer.Flush();
    }

    private static void Identity(Utf8JsonWriter writer, string authority, string kind, string name, string revision)
    {
        string digest = Digest($"program-kit.governed-identity/v1\n{authority}\n{kind}\n{name}\n{revision}");
        writer.WriteString("authority", authority);
        writer.WriteString("digest", digest);
        writer.WriteString("kind", kind);
        writer.WriteString("name", name);
        writer.WriteString("revision", revision);
    }

    private static void SafeValue(Utf8JsonWriter writer, string value)
    {
        writer.WriteStartObject();
        writer.WriteString("classification", "public");
        writer.WriteString("value", value);
        writer.WriteString("valueKind", "string");
        writer.WriteEndObject();
    }

    private static string Digest(string value) => $"sha256:{Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant()}";

    private static string Kebab<T>(T value)
        where T : struct, Enum
    {
        string text = value.ToString();
        StringBuilder result = new();
        for (int index = 0; index < text.Length; index++)
        {
            if (index > 0 && char.IsUpper(text[index])) result.Append('-');
            result.Append(char.ToLowerInvariant(text[index]));
        }

        return result.ToString();
    }
}
