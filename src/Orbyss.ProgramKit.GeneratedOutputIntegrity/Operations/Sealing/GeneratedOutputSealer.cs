using Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;
using Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Serialization;

namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Operations.Sealing;

/// <summary>Creates deterministic manifest and anchor bytes over generated payloads.</summary>
public sealed class GeneratedOutputSealer : IGeneratedOutputSealer
{
    /// <summary>Seals one complete generated payload set.</summary>
    public GeneratedOutputSeal Seal(
        IEnumerable<GeneratedOutputPayload> payloads)
    {
        ArgumentNullException.ThrowIfNull(payloads);
        var materialized = payloads
            .Select(static payload =>
            {
                ArgumentNullException.ThrowIfNull(payload);
                return payload with
                {
                    RelativePath =
                        GeneratedOutputPathPolicy.RequireNormalizedRelativePath(
                            payload.RelativePath),
                };
            })
            .OrderBy(static payload => payload.RelativePath, StringComparer.Ordinal)
            .ToArray();
        if (materialized.Length == 0)
        {
            throw new InvalidDataException(
                "A generated-output seal requires at least one payload file.");
        }

        for (var index = 1; index < materialized.Length; index++)
        {
            if (string.Equals(
                    materialized[index - 1].RelativePath,
                    materialized[index].RelativePath,
                    StringComparison.Ordinal))
            {
                throw new InvalidDataException(
                    "Generated-output payload paths must be unique.");
            }
        }

        var entries = materialized
            .Select(static payload =>
                new GeneratedOutputManifestEntry(
                    payload.RelativePath,
                    Digest(payload.Content.Span),
                    payload.Content.Length))
            .ToImmutableArray();
        var manifest = new GeneratedOutputManifest(
            GeneratedOutputIntegrityConstants.ManifestSchema,
            GeneratedOutputIntegrityConstants.FormatVersion,
            GeneratedOutputIntegrityConstants.Ownership,
            entries);
        var manifestBytes = GeneratedOutputIntegritySerializer.Write(manifest);
        var anchorBytes = CreateAnchorBytes(manifestBytes);
        var anchor = GeneratedOutputIntegritySerializer.ReadAnchor(
            anchorBytes.Span);
        return new GeneratedOutputSeal(
            manifest,
            manifestBytes,
            anchor,
            anchorBytes);
    }

    /// <inheritdoc />
    public ReadOnlyMemory<byte> CreateAnchorBytes(
        ReadOnlyMemory<byte> manifestBytes)
    {
        if (manifestBytes.IsEmpty)
        {
            throw new InvalidDataException(
                "Generated-output manifest bytes are required.");
        }

        var anchor = new GeneratedOutputAnchor(
            GeneratedOutputIntegrityConstants.AnchorSchema,
            GeneratedOutputIntegrityConstants.FormatVersion,
            GeneratedOutputIntegrityConstants.ManifestRelativePath,
            Digest(manifestBytes.Span));
        return GeneratedOutputIntegritySerializer.Write(anchor);
    }

    internal static string Digest(ReadOnlySpan<byte> bytes) =>
        string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(bytes)));
}
