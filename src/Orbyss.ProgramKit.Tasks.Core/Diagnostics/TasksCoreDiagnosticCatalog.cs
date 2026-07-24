namespace Orbyss.ProgramKit.Tasks.Core.Diagnostics;

/// <summary>Immutable Tasks.Core diagnostic definitions.</summary>
public static class TasksCoreDiagnosticCatalog
{
    /// <summary>Gets the complete Tasks.Core diagnostic catalog.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
    [
        Error(TasksCoreDiagnosticIds.InvalidTaskDefinition, "Invalid task definition"),
        Error(TasksCoreDiagnosticIds.InvalidTaskRequest, "Invalid task request"),
        Error(TasksCoreDiagnosticIds.InvalidTaskInstance, "Invalid task instance"),
        Error(TasksCoreDiagnosticIds.InvalidTaskAttempt, "Invalid task attempt"),
        Error(
            TasksCoreDiagnosticIds.InvalidTaskActivationBinding,
            "Invalid task activation binding"),
        Error(
            TasksCoreDiagnosticIds.InvalidTaskScheduleDefinition,
            "Invalid task schedule definition"),
        Error(TasksCoreDiagnosticIds.InvalidTaskOccurrence, "Invalid task occurrence"),
        Error(TasksCoreDiagnosticIds.InvalidTaskLifecycleView, "Invalid task lifecycle view"),
    ];

    private static ProgramKitDiagnosticDefinition Error(string id, string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
