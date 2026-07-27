namespace Orbyss.ProgramKit.DevContainers.Contracts.Mounts;

/// <summary>One explicit structured mount.</summary>
public sealed record DevContainerMount(
    DevContainerMountKind Kind,
    string? Source,
    string Target);
