using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Tasks.Core.Validation;
using Orbyss.ProgramKit.Tasks.Diagnostics;
using Orbyss.ProgramKit.Tasks.Middleware;
using Orbyss.ProgramKit.Tasks.Policies;
using Orbyss.ProgramKit.Tasks.Registration;

namespace Orbyss.ProgramKit.Tasks.Composition;

/// <summary>Default fail-closed immutable task registry factory.</summary>
public sealed class TaskRegistryFactory : ITaskRegistryFactory
{
    private readonly ITaskContractValidator taskContractValidator;
    private readonly IProgramKitSemanticValidator<ArtifactReference>
        referenceValidator;

    /// <summary>Initializes the factory with semantic contract validators.</summary>
    public TaskRegistryFactory(
        ITaskContractValidator taskContractValidator,
        IProgramKitSemanticValidator<ArtifactReference> referenceValidator)
    {
        this.taskContractValidator = taskContractValidator ??
            throw new ArgumentNullException(nameof(taskContractValidator));
        this.referenceValidator = referenceValidator ??
            throw new ArgumentNullException(nameof(referenceValidator));
    }

    /// <inheritdoc />
    public ITaskRegistry Create(TaskRegistrationSet registrations)
    {
        ArgumentNullException.ThrowIfNull(registrations);
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        var definitions = TaskRegistrationCollapser.Collapse(
            registrations.Definitions,
            static registration => registration.Definition.Revision,
            static (left, right) => left == right,
            "/definitions",
            diagnostics);
        var handlers = TaskRegistrationCollapser.Collapse(
            registrations.Handlers,
            static registration => registration.HandlerRevision,
            HandlerEquals,
            "/handlers",
            diagnostics);
        var bindings = TaskRegistrationCollapser.Collapse(
            registrations.Bindings,
            static registration => registration.Binding.Revision,
            static (left, right) => left == right,
            "/bindings",
            diagnostics);
        var features = TaskRegistrationCollapser.Collapse(
            registrations.Features,
            static registration => registration.FeatureRevision,
            static (left, right) => left == right,
            "/features",
            diagnostics);
        var middleware = TaskRegistrationCollapser.Collapse(
            registrations.Middleware,
            static registration => registration.Revision,
            MiddlewareEquals,
            "/middleware",
            diagnostics);
        var schedules = TaskRegistrationCollapser.Collapse(
            registrations.Schedules,
            static registration => registration.Schedule.Revision,
            ScheduleEquals,
            "/schedules",
            diagnostics);
        var calculators = TaskRegistrationCollapser.Collapse(
            registrations.Calculators,
            static registration => registration.Profile,
            CalculatorEquals,
            "/calculators",
            diagnostics);
        var occurrenceRequestFactories = TaskRegistrationCollapser.Collapse(
            registrations.OccurrenceRequestFactories,
            static registration => registration.ScheduleRevision,
            OccurrenceRequestFactoryEquals,
            "/occurrenceRequestFactories",
            diagnostics);
        var misfirePolicies = TaskRegistrationCollapser.Collapse(
            registrations.MisfirePolicies,
            static registration => registration.Revision,
            static (left, right) => left == right,
            "/misfirePolicies",
            diagnostics);
        var overlapPolicies = TaskRegistrationCollapser.Collapse(
            registrations.OverlapPolicies,
            static registration => registration.Revision,
            static (left, right) => left == right,
            "/overlapPolicies",
            diagnostics);

        ValidateDefinitions(definitions, diagnostics);
        ValidateHandlers(handlers, diagnostics);
        ValidateFeatures(features, diagnostics);
        ValidateMiddleware(middleware, diagnostics);
        ValidateSchedules(schedules, diagnostics);
        ValidateCalculators(calculators, diagnostics);
        ValidateOccurrenceRequestFactories(
            occurrenceRequestFactories,
            diagnostics);
        ValidateMisfirePolicies(misfirePolicies, diagnostics);
        ValidateOverlapPolicies(overlapPolicies, diagnostics);
        ValidateBindingsAndClosure(
            definitions,
            handlers,
            bindings,
            features,
            middleware,
            schedules,
            calculators,
            occurrenceRequestFactories,
            misfirePolicies,
            overlapPolicies,
            diagnostics);
        var dispatchOrder = TaskMiddlewareOrderer.Order(
            middleware,
            TaskMiddlewarePhase.Dispatch,
            diagnostics);
        var executionOrder = TaskMiddlewareOrderer.Order(
            middleware,
            TaskMiddlewarePhase.Execution,
            diagnostics);
        if (diagnostics.Count > 0)
        {
            throw TaskDiagnostics.Exception(diagnostics);
        }

        return new TaskRegistry(
            definitions,
            handlers,
            bindings,
            features,
            dispatchOrder,
            executionOrder,
            schedules,
            calculators,
            occurrenceRequestFactories,
            misfirePolicies,
            overlapPolicies);
    }

    private void ValidateDefinitions(
        ImmutableArray<TaskDefinitionRegistration> definitions,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in definitions)
        {
            AddResult(
                diagnostics,
                taskContractValidator.Validate(registration.Definition));
        }
    }

    private void ValidateHandlers(
        ImmutableArray<ITaskHandlerRegistration> handlers,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in handlers)
        {
            AddResult(
                diagnostics,
                referenceValidator.Validate(registration.HandlerRevision));
            if (!SemanticVersionRange.Validate(
                    registration.SupportedDefinitionVersions.Value).IsValid ||
                !IsClosedConcreteClass(registration.HandlerType) ||
                registration.RequestType.ContainsGenericParameters ||
                registration.ResponseType.ContainsGenericParameters)
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "A handler registration requires exact valid types and a supported definition range.",
                    "/handlers");
            }
        }
    }

    private void ValidateFeatures(
        ImmutableArray<TaskFeatureRegistration> features,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in features)
        {
            AddResult(
                diagnostics,
                referenceValidator.Validate(registration.FeatureRevision));
        }
    }

    private void ValidateMiddleware(
        ImmutableArray<TaskMiddlewareRegistration> middleware,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in middleware)
        {
            AddResult(
                diagnostics,
                referenceValidator.Validate(registration.Revision));
            var contractType = registration.Phase ==
                TaskMiddlewarePhase.Dispatch
                    ? typeof(ITaskDispatchMiddleware)
                    : typeof(ITaskExecutionMiddleware);
            if (!Enum.IsDefined(registration.Phase) ||
                !IsClosedConcreteClass(registration.MiddlewareType) ||
                !contractType.IsAssignableFrom(registration.MiddlewareType) ||
                registration.Before.IsDefault ||
                registration.After.IsDefault)
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "Task middleware requires a valid phase, closed implementation type, and initialized ordering.",
                    "/middleware");
            }
        }
    }

    private void ValidateSchedules(
        ImmutableArray<ITaskScheduleRegistration> schedules,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in schedules)
        {
            AddResult(
                diagnostics,
                taskContractValidator.Validate(registration.Schedule));
            if (registration.Descriptor is null ||
                registration.Descriptor.GetType() != registration.DescriptorType ||
                registration.DescriptorType.ContainsGenericParameters)
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "A task schedule requires one exact typed descriptor.",
                    "/schedules");
            }
        }
    }

    private void ValidateCalculators(
        ImmutableArray<ITaskOccurrenceCalculatorRegistration> calculators,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in calculators)
        {
            AddResult(
                diagnostics,
                referenceValidator.Validate(registration.Profile));
            if (!IsClosedConcreteClass(registration.CalculatorType) ||
                registration.DescriptorType.ContainsGenericParameters)
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "An occurrence calculator requires closed descriptor and implementation types.",
                    "/calculators");
            }
        }
    }

    private void ValidateOccurrenceRequestFactories(
        ImmutableArray<ITaskOccurrenceRequestFactoryRegistration> factories,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in factories)
        {
            AddResult(
                diagnostics,
                referenceValidator.Validate(registration.ScheduleRevision));
            if (!IsClosedConcreteClass(registration.FactoryType) ||
                registration.RequestType.ContainsGenericParameters)
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "An occurrence request factory requires exact closed request and implementation types.",
                    "/occurrenceRequestFactories");
            }
        }
    }

    private void ValidateMisfirePolicies(
        ImmutableArray<TaskMisfirePolicyRegistration> policies,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in policies)
        {
            AddResult(
                diagnostics,
                referenceValidator.Validate(registration.Revision));
            var bounded = registration.Kind ==
                TaskMisfirePolicyKind.CatchUpBounded;
            if (!Enum.IsDefined(registration.Kind) ||
                bounded != (registration.MaximumCatchUp > 0))
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "Catch-up requires one positive finite bound; other misfire policies require zero.",
                    "/misfirePolicies");
            }
        }
    }

    private void ValidateOverlapPolicies(
        ImmutableArray<TaskOverlapPolicyRegistration> policies,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        foreach (var registration in policies)
        {
            AddResult(
                diagnostics,
                referenceValidator.Validate(registration.Revision));
            if (!Enum.IsDefined(registration.Kind))
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.InvalidRegistration,
                    "An overlap policy requires one supported exact kind.",
                    "/overlapPolicies");
            }
        }
    }

    private void ValidateBindingsAndClosure(
        ImmutableArray<TaskDefinitionRegistration> definitions,
        ImmutableArray<ITaskHandlerRegistration> handlers,
        ImmutableArray<TaskActivationBindingRegistration> bindings,
        ImmutableArray<TaskFeatureRegistration> features,
        ImmutableArray<TaskMiddlewareRegistration> middleware,
        ImmutableArray<ITaskScheduleRegistration> schedules,
        ImmutableArray<ITaskOccurrenceCalculatorRegistration> calculators,
        ImmutableArray<ITaskOccurrenceRequestFactoryRegistration>
            occurrenceRequestFactories,
        ImmutableArray<TaskMisfirePolicyRegistration> misfirePolicies,
        ImmutableArray<TaskOverlapPolicyRegistration> overlapPolicies,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var definitionKeys = definitions.ToDictionary(
            static item => TaskRegistrationKey.Exact(
                item.Definition.Revision),
            StringComparer.Ordinal);
        var handlerKeys = handlers.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.HandlerRevision),
            StringComparer.Ordinal);
        var featureKeys = features.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.FeatureRevision),
            StringComparer.Ordinal);
        var middlewareKeys = middleware.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.Revision),
            StringComparer.Ordinal);
        var scheduleKeys = schedules.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.Schedule.Revision),
            StringComparer.Ordinal);
        var calculatorKeys = calculators.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.Profile),
            StringComparer.Ordinal);
        var requestFactoryKeys = occurrenceRequestFactories.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.ScheduleRevision),
            StringComparer.Ordinal);
        var misfirePolicyKeys = misfirePolicies.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.Revision),
            StringComparer.Ordinal);
        var overlapPolicyKeys = overlapPolicies.ToDictionary(
            static item => TaskRegistrationKey.Exact(item.Revision),
            StringComparer.Ordinal);

        foreach (var duplicate in bindings.GroupBy(
                     static item => TaskRegistrationKey.Exact(
                         item.Binding.DefinitionRevision),
                     StringComparer.Ordinal)
                 .Where(static group => group.Count() > 1))
        {
            TaskDiagnostics.Add(
                diagnostics,
                TaskDiagnosticIds.ConflictingRegistration,
                "A task definition selects more than one activation binding.",
                "/bindings");
        }

        foreach (var registration in bindings)
        {
            var binding = registration.Binding;
            AddResult(diagnostics, taskContractValidator.Validate(binding));
            var definitionKey = TaskRegistrationKey.Exact(
                binding.DefinitionRevision);
            var handlerKey = TaskRegistrationKey.Exact(
                binding.HandlerRevision);
            var featureKey = TaskRegistrationKey.Exact(
                binding.OwningFeatureRevision);
            if (!definitionKeys.TryGetValue(
                    definitionKey,
                    out var definition) ||
                !handlerKeys.TryGetValue(handlerKey, out var handler) ||
                !featureKeys.ContainsKey(featureKey))
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.MissingRegistrationDependency,
                    "A binding requires its exact definition, handler, and owning feature.",
                    "/bindings");
                continue;
            }

            if (!handler.SupportedDefinitionVersions.Contains(
                    definition.Definition.Revision.Version))
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.IncompatibleHandler,
                    "The selected handler does not support the exact task-definition version.",
                    "/bindings");
            }

            if (binding.MiddlewareRevisions.Any(
                    revision => !middlewareKeys.ContainsKey(
                        TaskRegistrationKey.Exact(revision))))
            {
                TaskDiagnostics.Add(
                    diagnostics,
                    TaskDiagnosticIds.MissingRegistrationDependency,
                    "A binding requires every selected exact middleware revision.",
                    "/bindings");
            }

            if (binding.ScheduleRevision is not null)
            {
                var scheduleKey = TaskRegistrationKey.Exact(
                    binding.ScheduleRevision);
                if (!scheduleKeys.TryGetValue(
                        scheduleKey,
                        out var schedule) ||
                    schedule.Schedule.ActivationBindingRevision !=
                    binding.Revision ||
                    schedule.Schedule.DefinitionRevision !=
                    binding.DefinitionRevision ||
                    !calculatorKeys.TryGetValue(
                        TaskRegistrationKey.Exact(
                            schedule.Schedule.OccurrenceCalculatorProfile),
                        out var calculator) ||
                    calculator.DescriptorType != schedule.DescriptorType ||
                    !requestFactoryKeys.ContainsKey(scheduleKey) ||
                    binding.MisfirePolicyRevision is null ||
                    !misfirePolicyKeys.ContainsKey(
                        TaskRegistrationKey.Exact(
                            binding.MisfirePolicyRevision)) ||
                    binding.OverlapPolicyRevision is null ||
                    !overlapPolicyKeys.ContainsKey(
                        TaskRegistrationKey.Exact(
                            binding.OverlapPolicyRevision)))
                {
                    TaskDiagnostics.Add(
                        diagnostics,
                        TaskDiagnosticIds.MissingRegistrationDependency,
                        "A scheduled binding requires an exact matching schedule, calculator profile, descriptor type, request factory, misfire policy, and overlap policy.",
                        "/bindings");
                }
            }
        }
    }

    private static bool HandlerEquals(
        ITaskHandlerRegistration left,
        ITaskHandlerRegistration right) =>
        left.HandlerRevision == right.HandlerRevision &&
        left.SupportedDefinitionVersions ==
            right.SupportedDefinitionVersions &&
        left.RequestType == right.RequestType &&
        left.ResponseType == right.ResponseType &&
        left.HandlerType == right.HandlerType;

    private static bool MiddlewareEquals(
        TaskMiddlewareRegistration left,
        TaskMiddlewareRegistration right) =>
        left.Revision == right.Revision &&
        left.Phase == right.Phase &&
        left.MiddlewareType == right.MiddlewareType &&
        left.Priority == right.Priority &&
        left.Before.SequenceEqual(right.Before) &&
        left.After.SequenceEqual(right.After);

    private static bool ScheduleEquals(
        ITaskScheduleRegistration left,
        ITaskScheduleRegistration right) =>
        left.Schedule == right.Schedule &&
        left.DescriptorType == right.DescriptorType &&
        Equals(left.Descriptor, right.Descriptor);

    private static bool CalculatorEquals(
        ITaskOccurrenceCalculatorRegistration left,
        ITaskOccurrenceCalculatorRegistration right) =>
        left.Profile == right.Profile &&
        left.DescriptorType == right.DescriptorType &&
        left.CalculatorType == right.CalculatorType &&
        left.RequiresPreviousTerminalCompletion ==
            right.RequiresPreviousTerminalCompletion;

    private static bool OccurrenceRequestFactoryEquals(
        ITaskOccurrenceRequestFactoryRegistration left,
        ITaskOccurrenceRequestFactoryRegistration right) =>
        left.ScheduleRevision == right.ScheduleRevision &&
        left.RequestType == right.RequestType &&
        left.FactoryType == right.FactoryType;

    private static bool IsClosedConcreteClass(Type type) =>
        type.IsClass &&
        !type.IsAbstract &&
        !type.ContainsGenericParameters;

    private static void AddResult(
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics,
        ProgramKitValidationResult result) =>
        diagnostics.AddRange(result.Diagnostics);
}
