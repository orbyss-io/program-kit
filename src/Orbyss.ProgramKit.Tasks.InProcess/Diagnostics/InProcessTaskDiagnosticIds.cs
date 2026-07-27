namespace Orbyss.ProgramKit.Tasks.InProcess.Diagnostics;

/// <summary>Stable in-process task diagnostic identifiers.</summary>
public static class InProcessTaskDiagnosticIds
{
    /// <summary>The volatile queue cannot accept more work.</summary>
    public const string QueueFull = "PKTIP001";

    /// <summary>No exact definition/binding/handler selection exists.</summary>
    public const string MissingSelection = "PKTIP002";

    /// <summary>The runtime is not accepting work.</summary>
    public const string NotAccepting = "PKTIP003";

    /// <summary>An idempotency claim already exists.</summary>
    public const string DuplicateRequest = "PKTIP004";

    /// <summary>A prior scheduled instance is no longer observable.</summary>
    public const string ScheduleStateUnavailable = "PKTIP005";
}
