using Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;

namespace Orbyss.ProgramKit.DevContainers.Contracts.Profiles;

/// <summary>
/// Generates one bounded Compose primary service from either an exact image or
/// an exact Dockerfile. It is not a general-purpose Compose model.
/// </summary>
public sealed record DevContainerComposeProfile(
    string Service,
    string WorkspaceFolder,
    string? Image,
    DevContainerOpaqueArtifact? Dockerfile,
    string BuildContext) : DevContainerProfile;
