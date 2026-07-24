using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Schedules.Calculation;

internal static class ScheduleCalculationGuard
{
    internal static void Validate<TDescriptor>(
        TaskOccurrenceCalculationRequest<TDescriptor> request)
        where TDescriptor : notnull
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentNullException.ThrowIfNull(request.Schedule);
        ArgumentNullException.ThrowIfNull(request.Descriptor);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(
            request.MaximumOccurrences);
        if (request.CursorExclusive > request.EvaluationInstant)
        {
            throw new ArgumentException(
                "The exclusive cursor cannot follow the evaluation instant.",
                nameof(request));
        }
    }
}
