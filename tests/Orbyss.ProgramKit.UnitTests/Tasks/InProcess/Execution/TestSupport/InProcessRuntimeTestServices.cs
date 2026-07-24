using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Activation;
using Orbyss.ProgramKit.Tasks.Composition;
using Orbyss.ProgramKit.Tasks.InProcess.Composition;
using Orbyss.ProgramKit.Tasks.Policies;
using Orbyss.ProgramKit.Tasks.Registration;
using Orbyss.ProgramKit.Tasks.Schedules.Calculation;
using Orbyss.ProgramKit.Tasks.Schedules.Descriptors;
using Orbyss.ProgramKit.UnitTests.Tasks.Composition.TestSupport;
using Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Scheduling.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Tasks.InProcess.Execution.TestSupport;

internal static class InProcessRuntimeTestServices
{
    internal static ServiceProvider Build(
        int queueCapacity = 4,
        ArtifactReference? runtimeRevision = null)
    {
        IServiceCollection services =
            CreateBaseServices<TestTaskHandler>();
        services.AddTaskActivationBinding(TasksCoreTestValues.Binding());
        SelectRuntime(
            services,
            queueCapacity,
            runtimeRevision: runtimeRevision);
        return services.BuildServiceProvider();
    }

    internal static ServiceProvider BuildWithDispatchMiddleware()
    {
        IServiceCollection services =
            CreateBaseServices<TestTaskHandler>();
        var selectedRevision = TestContractValues.Reference(
            "pkid:middleware:program-kit:selected-dispatch");
        var unselectedRevision = TestContractValues.Reference(
            "pkid:middleware:program-kit:unselected-dispatch");
        services.AddTaskActivationBinding(
            TasksCoreTestValues.Binding() with
            {
                MiddlewareRevisions = [selectedRevision],
            });
        services.AddSingleton<TestTaskMiddlewareTracker>();
        services.AddTaskMiddleware<SelectedTestDispatchMiddleware>(
            selectedRevision,
            TaskMiddlewarePhase.Dispatch);
        services.AddTaskMiddleware<UnselectedTestDispatchMiddleware>(
            unselectedRevision,
            TaskMiddlewarePhase.Dispatch);
        SelectRuntime(services, 4);
        return services.BuildServiceProvider();
    }

    internal static ServiceProvider BuildScheduled(TimeSpan delay)
    {
        IServiceCollection services =
            CreateBaseServices<TestTaskHandler>();
        var binding = TasksCoreTestValues.Binding(scheduled: true);
        services.AddTaskActivationBinding(binding);
        services.AddTaskSchedule(
            TasksCoreTestValues.Schedule(),
            new FixedDelayScheduleDescriptor(delay));
        services.AddTaskOccurrenceCalculator<
            FixedDelayScheduleDescriptor,
            FixedDelayOccurrenceCalculator>(
            TasksCoreTestValues.Schedule().OccurrenceCalculatorProfile);
        services.AddTaskOccurrenceRequestFactory<
            TestTaskRequestModel,
            TestTaskOccurrenceRequestFactory>(
            TasksCoreTestValues.Schedule().Revision);
        services.AddTaskMisfirePolicy(
            new TaskMisfirePolicyRegistration(
                binding.MisfirePolicyRevision!,
                TaskMisfirePolicyKind.FireOnceNow,
                0));
        services.AddTaskOverlapPolicy(
            new TaskOverlapPolicyRegistration(
                binding.OverlapPolicyRevision!,
                TaskOverlapPolicyKind.Skip));
        SelectRuntime(
            services,
            4,
            TimeSpan.FromDays(1));
        return services.BuildServiceProvider();
    }

    internal static ServiceProvider BuildBlocking(int queueCapacity)
    {
        IServiceCollection services =
            CreateBaseServices<TestBlockingTaskHandler>();
        services.AddTaskActivationBinding(TasksCoreTestValues.Binding());
        services.AddSingleton<TestTaskExecutionLatch>();
        services.AddSingleton<ITestTaskExecutionLatch>(
            static provider =>
                provider.GetRequiredService<TestTaskExecutionLatch>());
        SelectRuntime(services, queueCapacity);
        return services.BuildServiceProvider();
    }

    private static IServiceCollection CreateBaseServices<THandler>()
        where THandler : class,
            Orbyss.ProgramKit.Tasks.Core.Execution.ITaskHandler<
                TestTaskRequestModel,
                TestTaskResponseModel>
    {
        IServiceCollection services = new ServiceCollection();
        services.AddProgramKitTasks();
        services.AddTaskDefinition(TasksCoreTestValues.Definition());
        services.AddTaskFeature(
            TasksCoreTestValues.Binding().OwningFeatureRevision);
        services.AddTaskHandler<
            TestTaskRequestModel,
            TestTaskResponseModel,
            THandler>(
            TasksCoreTestValues.Binding().HandlerRevision,
            new SemanticVersionRange("[1.0.0]"));
        services.AddSingleton<TestTaskActivationScopeResolver>();
        services.AddSingleton<ITaskActivationScopeResolver>(
            static provider =>
                provider.GetRequiredService<
                    TestTaskActivationScopeResolver>());
        return services;
    }

    private static void SelectRuntime(
        IServiceCollection services,
        int queueCapacity,
        TimeSpan? pollingInterval = null,
        ArtifactReference? runtimeRevision = null) =>
        services.UseInProcessTaskRuntime(
            new InProcessTaskRuntimeOptions
            {
                RuntimeRevision =
                    runtimeRevision ??
                    TasksCoreTestValues.Binding().RuntimeRevision,
                QueueCapacity = queueCapacity,
                MaximumConcurrency = 1,
                TerminalRetention = TimeSpan.FromMinutes(1),
                IdempotencyRetention = TimeSpan.FromMinutes(1),
                SchedulePollingInterval =
                    pollingInterval ?? TimeSpan.FromSeconds(1),
            });
}
