namespace Orbyss.ProgramKit.Tasks.Policies;

/// <summary>Supported volatile handling while a scheduled instance is active.</summary>
public enum TaskOverlapPolicyKind
{
    /// <summary>Permit another accepted instance.</summary>
    Allow = 0,

    /// <summary>Do not submit an occurrence while an instance is active.</summary>
    Skip = 1,

    /// <summary>Retain at most one occurrence until the active instance terminates.</summary>
    QueueOne = 2,
}
