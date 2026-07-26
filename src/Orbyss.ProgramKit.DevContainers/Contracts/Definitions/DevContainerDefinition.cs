using Orbyss.ProgramKit.DevContainers.Contracts.Artifacts;
using Orbyss.ProgramKit.DevContainers.Contracts.Features;
using Orbyss.ProgramKit.DevContainers.Contracts.Lifecycle;
using Orbyss.ProgramKit.DevContainers.Contracts.Mounts;
using Orbyss.ProgramKit.DevContainers.Contracts.Ports;
using Orbyss.ProgramKit.DevContainers.Contracts.Profiles;

namespace Orbyss.ProgramKit.DevContainers.Contracts.Definitions;

/// <summary>Complete explicit input to deterministic Dev Container generation.</summary>
public sealed record DevContainerDefinition(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    string Name,
    DevContainerProfile Profile,
    ImmutableArray<DevContainerFeature> Features,
    ImmutableArray<DevContainerMount> Mounts,
    ImmutableArray<DevContainerForwardedPort> ForwardedPorts,
    string? ContainerUser,
    string? RemoteUser,
    ImmutableArray<DevContainerLifecycleCommand> LifecycleCommands,
    ImmutableArray<DevContainerOpaqueArtifact> Scripts);
