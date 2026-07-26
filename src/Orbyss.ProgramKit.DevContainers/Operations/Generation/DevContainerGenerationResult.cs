namespace Orbyss.ProgramKit.DevContainers.Operations.Generation;

/// <summary>Deterministic generated file set and complete tree digest.</summary>
public sealed record DevContainerGenerationResult(
    ImmutableArray<DevContainerGeneratedFile> Files,
    Sha256Digest OutputTreeDigest);
