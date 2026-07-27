using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Typed bridge for one explicit occurrence calculator profile.</summary>
public sealed class TaskOccurrenceCalculatorRegistration<
    TDescriptor,
    TCalculator> : ITaskOccurrenceCalculatorRegistration
    where TDescriptor : notnull
    where TCalculator : class, ITaskOccurrenceCalculator<TDescriptor>
{
    /// <summary>Initializes the typed calculator registration.</summary>
    public TaskOccurrenceCalculatorRegistration(ArtifactReference profile)
    {
        Profile = profile ??
            throw new ArgumentNullException(nameof(profile));
    }

    /// <inheritdoc />
    public ArtifactReference Profile { get; }

    /// <inheritdoc />
    public Type DescriptorType => typeof(TDescriptor);

    /// <inheritdoc />
    public Type CalculatorType => typeof(TCalculator);

    /// <inheritdoc />
    public bool RequiresPreviousTerminalCompletion =>
        typeof(ITaskTerminalCompletionOccurrenceCalculator<TDescriptor>)
            .IsAssignableFrom(typeof(TCalculator));

    /// <inheritdoc />
    public ValueTask ValidateDescriptorAsync(
        IServiceProvider services,
        object descriptor,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(services);
        if (descriptor is not TDescriptor typedDescriptor)
        {
            throw new ArgumentException(
                string.Concat(
                    "The schedule descriptor must be assignable to ",
                    typeof(TDescriptor).FullName,
                    "."),
                nameof(descriptor));
        }

        var calculator = services.GetRequiredService<TCalculator>();
        return calculator is
            ITaskScheduleDescriptorValidator<TDescriptor> validator
                ? validator.ValidateAsync(
                    typedDescriptor,
                    cancellationToken)
                : ValueTask.CompletedTask;
    }

    /// <inheritdoc />
    public ValueTask<TaskOccurrenceCalculation> CalculateAsync(
        IServiceProvider services,
        TaskScheduleDefinition schedule,
        object descriptor,
        DateTimeOffset referenceInstant,
        DateTimeOffset cursorExclusive,
        DateTimeOffset evaluationInstant,
        DateTimeOffset? previousTerminalCompletionInstant,
        int maximumOccurrences,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(services);
        if (descriptor is not TDescriptor typedDescriptor)
        {
            throw new ArgumentException(
                string.Concat(
                    "The schedule descriptor must be assignable to ",
                    typeof(TDescriptor).FullName,
                    "."),
                nameof(descriptor));
        }

        var calculator = services.GetRequiredService<TCalculator>();
        return calculator.CalculateAsync(
            new TaskOccurrenceCalculationRequest<TDescriptor>(
                schedule,
                typedDescriptor,
                referenceInstant,
                cursorExclusive,
                evaluationInstant,
                previousTerminalCompletionInstant,
                maximumOccurrences),
            cancellationToken);
    }
}
