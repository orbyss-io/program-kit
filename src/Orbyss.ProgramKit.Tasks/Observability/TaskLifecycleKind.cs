namespace Orbyss.ProgramKit.Tasks.Observability;

/// <summary>Observed task lifecycle transition kind.</summary>
public enum TaskLifecycleKind
{
    /// <summary>A request was accepted.</summary>
    Accepted,
    /// <summary>An attempt started.</summary>
    AttemptStarted,
    /// <summary>An attempt succeeded.</summary>
    Succeeded,
    /// <summary>An attempt failed terminally.</summary>
    Failed,
    /// <summary>An accepted instance became cancelled.</summary>
    Cancelled,
}
