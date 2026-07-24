using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Tasks.Core.Dispatching;
using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Scheduling;

namespace Orbyss.ProgramKit.Tasks.Registration;

/// <summary>Typed occurrence-to-normal-request registration bridge.</summary>
public sealed class TaskOccurrenceRequestFactoryRegistration<
    TRequest,
    TFactory> : ITaskOccurrenceRequestFactoryRegistration
    where TRequest : notnull
    where TFactory : class, ITaskOccurrenceRequestFactory<TRequest>
{
    /// <summary>Initializes one exact schedule factory registration.</summary>
    public TaskOccurrenceRequestFactoryRegistration(
        ArtifactReference scheduleRevision)
    {
        ScheduleRevision = scheduleRevision ??
            throw new ArgumentNullException(nameof(scheduleRevision));
    }

    /// <inheritdoc />
    public ArtifactReference ScheduleRevision { get; }

    /// <inheritdoc />
    public Type RequestType => typeof(TRequest);

    /// <inheritdoc />
    public Type FactoryType => typeof(TFactory);

    /// <inheritdoc />
    public async ValueTask<TaskDispatchResult> DispatchAsync(
        IServiceProvider services,
        ITaskDispatcher dispatcher,
        TaskOccurrence occurrence,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(services);
        ArgumentNullException.ThrowIfNull(dispatcher);
        ArgumentNullException.ThrowIfNull(occurrence);
        var factory = services.GetRequiredService<TFactory>();
        var request = await factory.CreateAsync(
            occurrence,
            cancellationToken).ConfigureAwait(false);
        if (request.OccurrenceRevision != occurrence.Revision ||
            request.DefinitionRevision != occurrence.DefinitionRevision)
        {
            throw new InvalidOperationException(
                "An occurrence request factory must preserve the exact occurrence and definition references.");
        }

        return await dispatcher.DispatchAsync(
            request,
            cancellationToken).ConfigureAwait(false);
    }
}
