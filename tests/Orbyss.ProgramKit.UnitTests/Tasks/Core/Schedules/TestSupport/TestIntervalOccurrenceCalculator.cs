namespace Orbyss.ProgramKit.UnitTests.Tasks.Core.Schedules.TestSupport;

internal sealed class TestIntervalOccurrenceCalculator :
    ITaskOccurrenceCalculator<TestIntervalDescriptor>
{
    public ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        TaskOccurrenceCalculationRequest<TestIntervalDescriptor> request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var next = request.CursorExclusive.Add(request.Descriptor.Interval);
        ImmutableArray<TaskOccurrence> occurrences =
            next <= request.EvaluationInstant
                ?
                [
                    TasksCoreTestValues.Occurrence() with
                    {
                        ScheduledFor = next,
                        EvaluatedAt = request.EvaluationInstant,
                    },
                ]
                : [];
        return ValueTask.FromResult(
            new TaskOccurrenceCalculation(
                request.Schedule.Revision,
                request.EvaluationInstant,
                occurrences));
    }
}
