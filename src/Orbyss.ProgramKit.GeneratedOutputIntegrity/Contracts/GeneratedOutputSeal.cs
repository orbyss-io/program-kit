namespace Orbyss.ProgramKit.GeneratedOutputIntegrity.Contracts;

/// <summary>Deterministic manifest and external-anchor bytes for a payload set.</summary>
public sealed record GeneratedOutputSeal(
    GeneratedOutputManifest Manifest,
    ReadOnlyMemory<byte> ManifestBytes,
    GeneratedOutputAnchor Anchor,
    ReadOnlyMemory<byte> AnchorBytes);
