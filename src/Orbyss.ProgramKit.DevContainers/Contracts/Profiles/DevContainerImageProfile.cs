namespace Orbyss.ProgramKit.DevContainers.Contracts.Profiles;

/// <summary>Uses one immutable digest-pinned container image.</summary>
/// <param name="Image">Exact OCI image reference including a SHA-256 digest.</param>
public sealed record DevContainerImageProfile(string Image) : DevContainerProfile;
