namespace Orbyss.ProgramKit.Tasks.Composition;

/// <summary>Coordinates one atomic task-registry freeze boundary.</summary>
public interface ITaskRegistryCoordinator
{
    /// <summary>Gets whether the selected registry has frozen.</summary>
    bool IsFrozen { get; }

    /// <summary>Gets the frozen registry or fails before freeze.</summary>
    ITaskRegistry GetCurrent();

    /// <summary>Validates and freezes all selected registrations.</summary>
    ITaskRegistry Freeze();
}
