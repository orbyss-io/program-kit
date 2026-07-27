namespace Orbyss.ProgramKit.DevContainers.Contracts.Lifecycle;

/// <summary>Finite Dev Container lifecycle stages supported by the profile.</summary>
public enum DevContainerLifecycleStage
{
    /// <summary>Runs on the host before container creation.</summary>
    Initialize = 0,

    /// <summary>Runs once when the container is created.</summary>
    OnCreate = 1,

    /// <summary>Runs when workspace content is made available or updated.</summary>
    UpdateContent = 2,

    /// <summary>Runs after container creation.</summary>
    PostCreate = 3,

    /// <summary>Runs after each container start.</summary>
    PostStart = 4,

    /// <summary>Runs after each attachment.</summary>
    PostAttach = 5,
}
