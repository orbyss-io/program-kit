namespace Orbyss.ProgramKit.Tasks.Policies;

/// <summary>Supported bounded handling for occurrences missed before evaluation.</summary>
public enum TaskMisfirePolicyKind
{
    /// <summary>Do not submit missed occurrences.</summary>
    Skip = 0,

    /// <summary>Submit at most one missed occurrence.</summary>
    FireOnceNow = 1,

    /// <summary>Submit missed occurrences up to an explicit finite bound.</summary>
    CatchUpBounded = 2,
}
