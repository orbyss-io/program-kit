using System.Collections.Immutable;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

namespace Orbyss.ProgramKit.Tasks.Schedules.Calculation;

/// <summary>Pure calculator for positive fixed-duration anchored intervals.</summary>
public sealed class AnchoredFixedIntervalOccurrenceCalculator :
    ITaskOccurrenceCalculator<AnchoredFixedIntervalScheduleDescriptor>,
    ITaskScheduleDescriptorValidator<
        AnchoredFixedIntervalScheduleDescriptor>
{
    /// <inheritdoc />
    public ValueTask ValidateAsync(
        AnchoredFixedIntervalScheduleDescriptor descriptor,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(descriptor);
        cancellationToken.ThrowIfCancellationRequested();
        ArgumentOutOfRangeException.ThrowIfLessThanOrEqual(
            descriptor.Period,
            TimeSpan.Zero);
        return ValueTask.CompletedTask;
    }

    /// <inheritdoc />
    public ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        TaskOccurrenceCalculationRequest<AnchoredFixedIntervalScheduleDescriptor>
            request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        ScheduleCalculationGuard.Validate(request);
        ArgumentOutOfRangeException.ThrowIfLessThanOrEqual(
            request.Descriptor.Period,
            TimeSpan.Zero);

        var sequence = FirstSequenceAfter(
            request.Descriptor.Anchor,
            request.Descriptor.Period,
            request.CursorExclusive);
        var occurrences = ImmutableArray.CreateBuilder<TaskOccurrence>();
        while (occurrences.Count < request.MaximumOccurrences)
        {
            var due = AddPeriods(
                request.Descriptor.Anchor,
                request.Descriptor.Period,
                sequence);
            if (due > request.EvaluationInstant)
            {
                break;
            }

            occurrences.Add(
                ScheduleOccurrenceFactory.Create(
                    request.Schedule,
                    sequence,
                    due,
                    request.EvaluationInstant));
            sequence = checked(sequence + 1);
        }

        return ValueTask.FromResult(
            new TaskOccurrenceCalculation(
                request.Schedule.Revision,
                request.EvaluationInstant,
                occurrences.ToImmutable()));
    }

    private static long FirstSequenceAfter(
        DateTimeOffset anchor,
        TimeSpan period,
        DateTimeOffset cursorExclusive)
    {
        if (cursorExclusive < anchor)
        {
            return 0;
        }

        var elapsedTicks = checked(
            cursorExclusive.UtcTicks - anchor.UtcTicks);
        return checked((elapsedTicks / period.Ticks) + 1);
    }

    private static DateTimeOffset AddPeriods(
        DateTimeOffset anchor,
        TimeSpan period,
        long sequence)
    {
        var ticks = checked(period.Ticks * sequence);
        return anchor.AddTicks(ticks);
    }
}
