using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Tasks.Diagnostics;

/// <summary>Immutable task-composition diagnostic definitions.</summary>
public static class TaskDiagnosticCatalog
{
    /// <summary>Gets the complete task-composition diagnostic catalog.</summary>
    public static ImmutableArray<ProgramKitDiagnosticDefinition> Definitions { get; } =
    [
        Error(TaskDiagnosticIds.InvalidRegistration, "Invalid task registration"),
        Error(
            TaskDiagnosticIds.ConflictingRegistration,
            "Conflicting task registration"),
        Error(
            TaskDiagnosticIds.MissingRegistrationDependency,
            "Missing task registration dependency"),
        Error(TaskDiagnosticIds.IncompatibleHandler, "Incompatible task handler"),
        Error(
            TaskDiagnosticIds.InvalidMiddlewareOrder,
            "Invalid task middleware order"),
        Error(TaskDiagnosticIds.RegistryNotFrozen, "Task registry is not frozen"),
        Error(
            TaskDiagnosticIds.RegistrationAfterFreeze,
            "Task registration after freeze"),
        Error(
            TaskDiagnosticIds.ActivationResolutionFailed,
            "Task activation resolution failed"),
    ];

    private static ProgramKitDiagnosticDefinition Error(
        string id,
        string title) =>
        new(id, ProgramKitDiagnosticSeverity.Error, title);
}
