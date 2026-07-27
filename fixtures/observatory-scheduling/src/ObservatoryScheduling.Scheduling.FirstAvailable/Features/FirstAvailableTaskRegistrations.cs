using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Tasks.Composition;
using Orbyss.ProgramKit.Tasks.Registration;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Calculation;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;
using ObservatoryScheduling.Core.Tasks;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Applies the feature-owned task registrations to one selected shell.</summary>
public static class FirstAvailableTaskRegistrations
{
    /// <summary>Registers definitions, handler, middleware, activation, and schedule exactly once.</summary>
    public static void Register(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        _ = services.AddProgramKitTasks();
        services
            .AddTaskDefinition(FirstAvailableTaskContracts.Definition)
            .AddTaskFeature(FirstAvailableTaskContracts.FeatureRevision)
            .AddTaskHandler<
                ScheduleViewingTaskRequest,
                ScheduleViewingTaskResponse,
                ScheduleViewingTaskHandler>(
                FirstAvailableTaskContracts.HandlerRevision,
                new SemanticVersionRange("[1.0.0,2.0.0)"))
            .AddTaskMiddleware<ScheduleViewingTaskDispatchMiddleware>(
                FirstAvailableTaskContracts.MiddlewareRevision,
                TaskMiddlewarePhase.Dispatch)
            .AddTaskActivationBinding(FirstAvailableTaskContracts.Binding)
            .AddTaskSchedule(
                FirstAvailableTaskContracts.Schedule,
                FirstAvailableTaskContracts.ScheduleDescriptor)
            .AddTaskOccurrenceCalculator<
                CronosScheduleDescriptor,
                CronosOccurrenceCalculator>(
                FirstAvailableTaskContracts.CronosProfile)
            .AddTaskMisfirePolicy(FirstAvailableTaskContracts.MisfirePolicy)
            .AddTaskOverlapPolicy(FirstAvailableTaskContracts.OverlapPolicy)
            .AddTaskOccurrenceRequestFactory<
                ScheduleViewingTaskRequest,
                ScheduledViewingRequestFactory>(
                FirstAvailableTaskContracts.Schedule.Revision);
    }
}
