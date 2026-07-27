using System.Collections.Immutable;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

namespace Orbyss.ProgramKit.Tasks.Schedules.Calculation;

/// <summary>Pure calculator for one non-negative delayed occurrence.</summary>
public sealed class DelayOnceOccurrenceCalculator :
    ITaskOccurrenceCalculator<DelayOnceScheduleDescriptor>,
    ITaskScheduleDescriptorValidator<DelayOnceScheduleDescriptor>
{
    /// <inheritdoc />
    public ValueTask ValidateAsync(
        DelayOnceScheduleDescriptor descriptor,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        cancellationToken.ThrowIfCancellationRequested();
        ArgumentOutOfRangeException.ThrowIfLessThan(
            descriptor.Delay,
            TimeSpan.Zero);
        return ValueTask.CompletedTask;
    }

    /// <inheritdoc />
    public ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        TaskOccurrenceCalculationRequest<DelayOnceScheduleDescriptor> request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        ScheduleCalculationGuard.Validate(request);
        ArgumentOutOfRangeException.ThrowIfLessThan(
            request.Descriptor.Delay,
            TimeSpan.Zero);
        var due = request.ReferenceInstant.Add(request.Descriptor.Delay);
        ImmutableArray<TaskOccurrence> occurrences =
            due > request.CursorExclusive &&
            due <= request.EvaluationInstant
                ?
                [
                    ScheduleOccurrenceFactory.Create(
                        request.Schedule,
                        0,
                        due,
                        request.EvaluationInstant),
                ]
                : [];
        return ValueTask.FromResult(
            new TaskOccurrenceCalculation(
                request.Schedule.Revision,
                request.EvaluationInstant,
                occurrences));
    }
}
