namespace Orbyss.ProgramKit.DevContainers.Operations.Generation;

/// <summary>One deterministic output file relative to the caller-owned root.</summary>
public sealed record DevContainerGeneratedFile(
    string RelativePath,
    ImmutableArray<byte> Content);
