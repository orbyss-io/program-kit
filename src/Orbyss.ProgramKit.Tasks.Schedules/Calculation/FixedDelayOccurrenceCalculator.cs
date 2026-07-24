using System.Collections.Immutable;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

namespace Orbyss.ProgramKit.Tasks.Schedules.Calculation;

/// <summary>
/// Pure calculator for the next positive delay after terminal completion.
/// </summary>
public sealed class FixedDelayOccurrenceCalculator :
    ITaskTerminalCompletionOccurrenceCalculator<
        FixedDelayScheduleDescriptor>,
    ITaskScheduleDescriptorValidator<FixedDelayScheduleDescriptor>
{
    /// <inheritdoc />
    public ValueTask ValidateAsync(
        FixedDelayScheduleDescriptor descriptor,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        cancellationToken.ThrowIfCancellationRequested();
        ArgumentOutOfRangeException.ThrowIfLessThanOrEqual(
            descriptor.Delay,
            TimeSpan.Zero);
        return ValueTask.CompletedTask;
    }

    /// <inheritdoc />
    public ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        TaskOccurrenceCalculationRequest<FixedDelayScheduleDescriptor> request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        ScheduleCalculationGuard.Validate(request);
        ArgumentOutOfRangeException.ThrowIfLessThanOrEqual(
            request.Descriptor.Delay,
            TimeSpan.Zero);
        var basis = request.PreviousTerminalCompletionInstant ??
            request.ReferenceInstant;
        var due = basis.Add(request.Descriptor.Delay);
        ImmutableArray<TaskOccurrence> occurrences =
            due > request.CursorExclusive &&
            due <= request.EvaluationInstant
                ?
                [
                    ScheduleOccurrenceFactory.Create(
                        request.Schedule,
                        due.UtcTicks,
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
