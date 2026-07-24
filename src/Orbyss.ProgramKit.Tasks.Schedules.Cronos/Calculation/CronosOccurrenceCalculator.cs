using System.Collections.Immutable;
using Cronos;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Validation;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Calculation;

/// <summary>Pure occurrence calculator for the selected cronos/0.13 dialect.</summary>
public sealed class CronosOccurrenceCalculator :
    ITaskOccurrenceCalculator<CronosScheduleDescriptor>,
    ITaskScheduleDescriptorValidator<CronosScheduleDescriptor>
{
    /// <inheritdoc />
    public ValueTask ValidateAsync(
        CronosScheduleDescriptor descriptor,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        _ = CronosDescriptorGuard.Validate(descriptor);
        return ValueTask.CompletedTask;
    }

    /// <inheritdoc />
    public ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        TaskOccurrenceCalculationRequest<CronosScheduleDescriptor> request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        if (request.MaximumOccurrences <= 0 ||
            request.CursorExclusive > request.EvaluationInstant ||
            request.Descriptor.Profile !=
                request.Schedule.OccurrenceCalculatorProfile ||
            request.EvaluationInstant <
                request.Descriptor.TimeZoneEvidence.HorizonStart ||
            request.EvaluationInstant >
                request.Descriptor.TimeZoneEvidence.HorizonEnd)
        {
            throw new ArgumentException(
                "Cron occurrence calculation requires matching profile, positive bound, ordered instants, and an evaluation instant inside the selected evidence horizon.",
                nameof(request));
        }

        var zone = CronosDescriptorGuard.Validate(request.Descriptor);
        CronExpression expression = CronosDescriptorGuard.Parse(
            request.Descriptor);
        var occurrences = ImmutableArray.CreateBuilder<TaskOccurrence>();
        var cursor = request.CursorExclusive;
        while (occurrences.Count < request.MaximumOccurrences)
        {
            var next = expression.GetNextOccurrence(
                cursor,
                zone,
                inclusive: false);
            if (next is null || next.Value > request.EvaluationInstant)
            {
                break;
            }

            occurrences.Add(
                CronosOccurrenceFactory.Create(
                    request.Schedule,
                    next.Value.UtcTicks,
                    next.Value,
                    request.EvaluationInstant));
            cursor = next.Value;
        }

        return ValueTask.FromResult(
            new TaskOccurrenceCalculation(
                request.Schedule.Revision,
                request.EvaluationInstant,
                occurrences.ToImmutable()));
    }
}
