namespace Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;

/// <summary>
/// Human-owned opaque artifact whose exact bytes and non-secret classification
/// are asserted by the input owner and verified against the supplied digest.
/// </summary>
public sealed record DevContainerOpaqueArtifact(
    string RelativePath,
    ImmutableArray<byte> Content,
    Sha256Digest Digest,
    bool AttestedSecretFree);
