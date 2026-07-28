using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Serialization;

internal static class GeneratedOutputIntegritySerializer
{
    internal static ReadOnlyMemory<byte> Write(
        GeneratedOutputManifest manifest) =>
        WithTerminalNewline(
            JsonSerializer.SerializeToUtf8Bytes(
                manifest,
                GeneratedOutputIntegrityJsonContext.Default.GeneratedOutputManifest));

    internal static ReadOnlyMemory<byte> Write(
        GeneratedOutputAnchor anchor) =>
        WithTerminalNewline(
            JsonSerializer.SerializeToUtf8Bytes(
                anchor,
                GeneratedOutputIntegrityJsonContext.Default.GeneratedOutputAnchor));

    internal static GeneratedOutputManifest ReadManifest(
        ReadOnlySpan<byte> bytes) =>
        JsonSerializer.Deserialize(
            bytes,
            GeneratedOutputIntegrityJsonContext.Default.GeneratedOutputManifest) ??
        throw new JsonException("The generated-output manifest is null.");

    internal static GeneratedOutputAnchor ReadAnchor(
        ReadOnlySpan<byte> bytes) =>
        JsonSerializer.Deserialize(
            bytes,
            GeneratedOutputIntegrityJsonContext.Default.GeneratedOutputAnchor) ??
        throw new JsonException("The generated-output anchor is null.");

    private static ReadOnlyMemory<byte> WithTerminalNewline(byte[] bytes)
    {
        using MemoryStream stream = new(bytes.Length + 1);
        foreach (var value in bytes)
        {
            if (value != (byte)'\r')
            {
                stream.WriteByte(value);
            }
        }

        stream.WriteByte((byte)'\n');
        return stream.ToArray();
    }
}
