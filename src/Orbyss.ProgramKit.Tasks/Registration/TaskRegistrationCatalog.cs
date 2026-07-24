using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Tasks.Composition;
using Orbyss.ProgramKit.Tasks.Diagnostics;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Default thread-safe mutable-before-freeze registration catalog.</summary>
internal sealed class TaskRegistrationCatalog : ITaskRegistrationCatalog
{
    private readonly Lock gate = new();
    private readonly List<TaskDefinitionRegistration> definitions = [];
    private readonly List<ITaskHandlerRegistration> handlers;
    private readonly List<TaskActivationBindingRegistration> bindings = [];
    private readonly List<TaskFeatureRegistration> features = [];
    private readonly List<TaskMiddlewareRegistration> middleware = [];
    private readonly List<ITaskScheduleRegistration> schedules = [];
    private readonly List<ITaskOccurrenceCalculatorRegistration> calculators;
    private readonly List<ITaskOccurrenceRequestFactoryRegistration>
        occurrenceRequestFactories;
    private readonly List<TaskMisfirePolicyRegistration> misfirePolicies = [];
    private readonly List<TaskOverlapPolicyRegistration> overlapPolicies = [];
    private bool isFrozen;

    internal TaskRegistrationCatalog(
        List<ITaskHandlerRegistration> handlers,
        List<ITaskOccurrenceCalculatorRegistration> calculators,
        List<ITaskOccurrenceRequestFactoryRegistration>
            occurrenceRequestFactories)
    {
        this.handlers = handlers;
        this.calculators = calculators;
        this.occurrenceRequestFactories = occurrenceRequestFactories;
    }

    /// <inheritdoc />
    public bool IsFrozen
    {
        get
        {
            lock (gate)
            {
                return isFrozen;
            }
        }
    }

    /// <inheritdoc />
    public void Add(TaskDefinitionRegistration registration) =>
        AddCore(definitions, registration);

    /// <inheritdoc />
    public void Add(ITaskHandlerRegistration registration) =>
        AddCore(handlers, registration);

    /// <inheritdoc />
    public void Add(TaskActivationBindingRegistration registration) =>
        AddCore(bindings, registration);

    /// <inheritdoc />
    public void Add(TaskFeatureRegistration registration) =>
        AddCore(features, registration);

    /// <inheritdoc />
    public void Add(TaskMiddlewareRegistration registration) =>
        AddCore(middleware, registration);

    /// <inheritdoc />
    public void Add(ITaskScheduleRegistration registration) =>
        AddCore(schedules, registration);

    /// <inheritdoc />
    public void Add(ITaskOccurrenceCalculatorRegistration registration) =>
        AddCore(calculators, registration);

    /// <inheritdoc />
    public void Add(ITaskOccurrenceRequestFactoryRegistration registration) =>
        AddCore(occurrenceRequestFactories, registration);

    /// <inheritdoc />
    public void Add(TaskMisfirePolicyRegistration registration) =>
        AddCore(misfirePolicies, registration);

    /// <inheritdoc />
    public void Add(TaskOverlapPolicyRegistration registration) =>
        AddCore(overlapPolicies, registration);

    /// <inheritdoc />
    public void Import(TaskRegistrationSet registrations)
    {
        ArgumentNullException.ThrowIfNull(registrations);
        lock (gate)
        {
            EnsureMutable();
            definitions.AddRange(registrations.Definitions);
            handlers.AddRange(registrations.Handlers);
            bindings.AddRange(registrations.Bindings);
            features.AddRange(registrations.Features);
            middleware.AddRange(registrations.Middleware);
            schedules.AddRange(registrations.Schedules);
            calculators.AddRange(registrations.Calculators);
            occurrenceRequestFactories.AddRange(
                registrations.OccurrenceRequestFactories);
            misfirePolicies.AddRange(registrations.MisfirePolicies);
            overlapPolicies.AddRange(registrations.OverlapPolicies);
        }
    }

    /// <inheritdoc />
    public TaskRegistrationSet Export()
    {
        lock (gate)
        {
            return ExportCore();
        }
    }

    /// <inheritdoc />
    public ITaskRegistry Freeze(ITaskRegistryFactory factory)
    {
        ArgumentNullException.ThrowIfNull(factory);
        lock (gate)
        {
            if (isFrozen)
            {
                return factory.Create(ExportCore());
            }

            var registry = factory.Create(ExportCore());
            isFrozen = true;
            return registry;
        }
    }

    private void AddCore<TRegistration>(
        List<TRegistration> target,
        TRegistration registration)
        where TRegistration : class
    {
        ArgumentNullException.ThrowIfNull(registration);
        lock (gate)
        {
            EnsureMutable();
            target.Add(registration);
        }
    }

    private TaskRegistrationSet ExportCore() =>
        new(
            [.. definitions],
            [.. handlers],
            [.. bindings],
            [.. features],
            [.. middleware],
            [.. schedules],
            [.. calculators],
            [.. occurrenceRequestFactories],
            [.. misfirePolicies],
            [.. overlapPolicies]);

    private void EnsureMutable()
    {
        if (!isFrozen)
        {
            return;
        }

        throw new TaskCompositionException(
            "Task registration is closed because the registry is frozen.",
            ProgramKitValidationResult.From(
            [
                new ProgramKitDiagnostic(
                    TaskDiagnosticIds.RegistrationAfterFreeze,
                    ProgramKitDiagnosticSeverity.Error,
                    "Task registration after freeze is forbidden.",
                    "/registrations"),
            ]));
    }
}
