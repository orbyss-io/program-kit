namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Constrains package or tool restore during an execution.</summary>
public enum RestoreAccessPolicy
{
    /// <summary>Forbids dependency restore.</summary>
    Denied,
    /// <summary>Permits restore only from an exact lock.</summary>
    LockedOnly,
}
