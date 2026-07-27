using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Tasks.Diagnostics;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Composition;

/// <summary>Default task-registry freeze coordinator.</summary>
internal sealed class TaskRegistryCoordinator : ITaskRegistryCoordinator
{
    private readonly ITaskRegistrationCatalog catalog;
    private readonly ITaskRegistryFactory factory;

    /// <summary>Initializes the coordinator with its catalog and factory.</summary>
    public TaskRegistryCoordinator(
        ITaskRegistrationCatalog catalog,
        ITaskRegistryFactory factory)
    {
        this.catalog = catalog ??
            throw new ArgumentNullException(nameof(catalog));
        this.factory = factory ??
            throw new ArgumentNullException(nameof(factory));
    }

    /// <inheritdoc />
    public bool IsFrozen => catalog.IsFrozen;

    /// <inheritdoc />
    public ITaskRegistry GetCurrent() =>
        IsFrozen
            ? catalog.Freeze(factory)
            : throw new TaskCompositionException(
                "The task registry has not frozen.",
                ProgramKitValidationResult.From(
                [
                    new ProgramKitDiagnostic(
                        TaskDiagnosticIds.RegistryNotFrozen,
                        ProgramKitDiagnosticSeverity.Error,
                        "Task execution before registry freeze is forbidden.",
                        "/registry"),
                ]));

    /// <inheritdoc />
    public ITaskRegistry Freeze() => catalog.Freeze(factory);
}
