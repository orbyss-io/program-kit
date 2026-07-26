namespace Orbyss.ProgramKit.DevContainers.Contracts.Mounts;

/// <summary>Finite mount kinds in the Program Kit Dev Container profile.</summary>
public enum DevContainerMountKind
{
    /// <summary>A workspace-rooted bind mount.</summary>
    Bind = 0,

    /// <summary>A named container volume.</summary>
    Volume = 1,
}
