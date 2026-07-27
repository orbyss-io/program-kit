using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>Pure controlled-time occurrence calculation for one typed descriptor.</summary>
/// <typeparam name="TDescriptor">The typed schedule descriptor model.</typeparam>
public interface ITaskOccurrenceCalculator<TDescriptor>
    where TDescriptor : notnull
{
    /// <summary>Calculates ordered occurrences without reading a clock or executing work.</summary>
    ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        TaskOccurrenceCalculationRequest<TDescriptor> request,
        CancellationToken cancellationToken);
}
