using Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;

namespace Orbyss.ProgramKit.DevContainers.Contracts.Profiles;

/// <summary>Uses one exact opaque Dockerfile and explicit build context.</summary>
public sealed record DevContainerDockerfileProfile(
    DevContainerOpaqueArtifact Dockerfile,
    string BuildContext) : DevContainerProfile;
